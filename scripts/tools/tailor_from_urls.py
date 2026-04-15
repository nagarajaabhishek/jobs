#!/usr/bin/env python3
"""
Fetch JDs into jd_cache, optionally run JobEvaluator, then TailorAgent for each URL.

Usage (repo root):
  python3 scripts/tools/tailor_from_urls.py "https://..." "https://..."
  python3 scripts/tools/tailor_from_urls.py --file urls.txt
  # Default: tailor-only (no job-fit LLM). Use --also-eval to run evaluate_single_job first.
  python3 scripts/tools/tailor_from_urls.py --also-eval "https://..."
  # Manual_JD_Tailor: B = job URLs; 'Recommended Resume' column (auto-added after F on old tabs) = optional hint
  python3 scripts/tools/tailor_from_urls.py --from-tailor-tab
  # Skip TailorAgent QA/generate_resume; produce YAML only
  python3 scripts/tools/tailor_from_urls.py --from-tailor-tab --ensure-tailor-tab --skip-tailor-validation
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import math
import os
import re
import sys
import time
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator  # noqa: E402
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient  # noqa: E402
from apps.cli.legacy.core.jd_cache_helpers import ensure_jd_cached  # noqa: E402
from core_agents.resume_agent.tailor import TailorAgent  # noqa: E402


def _read_urls(args: argparse.Namespace) -> list[str]:
    raw: list[str] = []
    if getattr(args, "file", None):
        path = args.file
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    raw.append(line)
    if args.urls:
        raw.extend(args.urls)
    seen = set()
    out: list[str] = []
    for u in raw:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _resume_artifact_state(path_yaml: str | None, *, run_started_ts: float) -> tuple[bool, str]:
    """
    Returns (resume_generated, message).
    """
    if not path_yaml:
        return False, "Tailoring returned no YAML path."
    if not os.path.isfile(path_yaml):
        return False, "Tailored YAML file not found on disk."
    try:
        with open(path_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        meta = data.get("meta") if isinstance(data, dict) else {}
        rel_tex = str((meta or {}).get("filename") or "").strip()
        if not rel_tex:
            return False, "meta.filename missing in tailored YAML."
        resume_root = os.path.join(PROJECT_ROOT, "core_agents", "resume_agent")
        tex_path = os.path.normpath(os.path.join(resume_root, rel_tex))
        pdf_path = os.path.splitext(tex_path)[0] + ".pdf"
        pdf_new = os.path.isfile(pdf_path) and os.path.getmtime(pdf_path) >= (run_started_ts - 1.0)
        tex_new = os.path.isfile(tex_path) and os.path.getmtime(tex_path) >= (run_started_ts - 1.0)
        if pdf_new:
            return True, ""
        if tex_new:
            return False, f"TeX generated but PDF missing: {pdf_path}"
        if os.path.isfile(pdf_path):
            return False, f"PDF exists from earlier run (not regenerated this pass): {pdf_path}"
        if os.path.isfile(tex_path):
            return False, f"TeX exists from earlier run (not regenerated this pass): {tex_path}"
        return False, f"No TeX/PDF found at expected path: {tex_path}"
    except Exception as e:
        return False, f"Could not inspect tailored artifacts: {e}"


def _clean_text(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text or "")
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def _cosine_similarity(text1: str, text2: str) -> float:
    vec1 = Counter((text1 or "").split())
    vec2 = Counter((text2 or "").split())
    if not vec1 or not vec2:
        return 0.0
    inter = set(vec1.keys()) & set(vec2.keys())
    num = sum(vec1[k] * vec2[k] for k in inter)
    den = math.sqrt(sum(v * v for v in vec1.values())) * math.sqrt(sum(v * v for v in vec2.values()))
    if not den:
        return 0.0
    return float(num) / den


def _ats_like_score(resume_text: str, jd_text: str) -> float:
    clean_resume = _clean_text(resume_text)
    clean_jd = _clean_text(jd_text)
    jd_words = set(clean_jd.split())
    stop_words = {
        "the", "and", "to", "of", "a", "in", "is", "that", "for", "it", "as", "was", "with", "on", "are", "be",
        "this", "an", "at", "by", "from", "or", "which", "but", "not", "what", "all", "were", "we", "when", "your",
        "can", "said", "there", "use", "each", "if", "will", "up", "other", "about", "out", "many", "then", "them",
        "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look", "two", "more",
    }
    keywords = {w for w in jd_words if w not in stop_words and len(w) > 2}
    res_words = set(clean_resume.split())
    kw_score = (len(keywords & res_words) / len(keywords) * 100.0) if keywords else 0.0
    sim_score = _cosine_similarity(clean_resume, clean_jd) * 100.0
    return (kw_score * 0.6) + (sim_score * 0.4)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _compare_tailored_vs_generic(
    *,
    tailor: TailorAgent,
    path_yaml: str | None,
    jd_text: str,
    recommended_resume: str,
) -> tuple[str, str, str, str, str]:
    """
    Returns (verdict, reason, tailored_score, generic_score, use_resume).
    """
    if not path_yaml or not os.path.isfile(path_yaml):
        return ("", "Tailored YAML missing; comparison skipped.", "", "", "")

    try:
        tailored_text = _read_text(path_yaml)
    except Exception as e:
        return ("", f"Could not read tailored YAML: {e}", "", "", "")

    rr_base = tailor._resolve_base_role_yaml_for_recommendation(recommended_resume)  # pylint: disable=protected-access
    base_yaml = (rr_base or tailor._base_role_yaml).strip()  # pylint: disable=protected-access
    generic_path = os.path.join(tailor.base_dir, "data", tailor._profile, base_yaml)  # pylint: disable=protected-access
    if not os.path.isfile(generic_path):
        return ("", f"Generic base YAML not found: {base_yaml}", "", "", "")

    try:
        generic_text = _read_text(generic_path)
    except Exception as e:
        return ("", f"Could not read generic YAML: {e}", "", "", "")

    t_score = _ats_like_score(tailored_text, jd_text)
    g_score = _ats_like_score(generic_text, jd_text)
    diff = t_score - g_score
    if diff > 0.5:
        verdict = "TAILORED_BETTER"
        use_resume = "TAILORED"
        reason = f"Tailored scored higher against JD by {diff:.2f} points."
    elif diff < -0.5:
        verdict = "GENERIC_BETTER"
        use_resume = "GENERIC_RECOMMENDED"
        reason = f"Generic recommended scored higher against JD by {abs(diff):.2f} points."
    else:
        verdict = "TIE"
        use_resume = "TAILORED"
        reason = "Scores are effectively tied; defaulting to tailored resume."
    return (verdict, reason, f"{t_score:.2f}", f"{g_score:.2f}", use_resume)


def main() -> int:
    ap = argparse.ArgumentParser(description="URL-driven JD cache + optional eval + tailoring.")
    ap.add_argument("urls", nargs="*", help="Job posting URLs")
    ap.add_argument("--file", "-f", help="Text file: one URL per line (# comments allowed)")
    ap.add_argument(
        "--also-eval",
        action="store_true",
        help="Run evaluate_single_job (LLM job fit); default is tailor-only after JD fetch.",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--profile", default="", help="Override resume.profile (default: Abhishek)")
    ap.add_argument("--base-yaml", default="", help="Override resume.base_role_yaml filename")
    ap.add_argument(
        "--from-tailor-tab",
        action="store_true",
        help="Read job URLs from the Manual_JD_Tailor worksheet (Job Link column).",
    )
    ap.add_argument(
        "--ensure-tailor-tab",
        action="store_true",
        help="Create the Manual_JD_Tailor tab (with headers) if it does not exist.",
    )
    ap.add_argument(
        "--skip-tailor-validation",
        action="store_true",
        help="Skip TailorAgent resume QA/generate_resume and output tailored YAML only.",
    )
    ap.add_argument(
        "--validate-variants",
        dest="validate_variants",
        action="store_true",
        help="After tailoring, compare tailored YAML vs generic recommended YAML against JD and write winner.",
    )
    ap.add_argument(
        "--no-validate-variants",
        dest="validate_variants",
        action="store_false",
        help="Disable post-tailor variant comparison.",
    )
    ap.set_defaults(validate_variants=None)
    args = ap.parse_args()
    skip_eval = not args.also_eval

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    client = GoogleSheetsClient()
    client.connect()
    ensure_tailor_tab = bool(args.ensure_tailor_tab or args.from_tailor_tab)
    if ensure_tailor_tab:
        client.ensure_manual_jd_tailor_worksheet()

    if args.from_tailor_tab:
        jobs = client.read_manual_jd_tailor_jobs()
        if not jobs:
            print(
                "No URLs on Manual_JD_Tailor tab (Job Link column).",
                file=sys.stderr,
            )
            return 2
    else:
        url_list = _read_urls(args)
        jobs = [{"url": u, "recommended_resume": ""} for u in url_list]
    evaluator = JobEvaluator()
    tailor = TailorAgent(
        profile=args.profile.strip() or None,
        base_role_yaml=args.base_yaml.strip() or None,
    )

    validate_variants = args.validate_variants if args.validate_variants is not None else bool(args.from_tailor_tab)

    for job in jobs:
        url = job["url"]
        sheet_rec = (job.get("recommended_resume") or "").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok, jd_msg = ensure_jd_cached(client, url, project_root=PROJECT_ROOT)
        if not ok:
            line = {"url": url, "error": jd_msg}
            if args.from_tailor_tab:
                client.update_manual_jd_tailor_result(
                    url=url,
                    status="JD_FETCH_FAILED",
                    tailored_yaml="",
                    error=jd_msg,
                    last_processed=now,
                )
            print(json.dumps(line, ensure_ascii=False) if args.json else f"\n{url}\n  SKIP: {jd_msg}")
            continue

        jd_text = (client.get_jd_for_url(url) or "").strip()
        score = 95
        eval_out = None
        rec_for_tailor = sheet_rec
        if not skip_eval:
            try:
                eval_out = evaluator.evaluate_single_job(url)
            except Exception as e:
                line = {"url": url, "error": str(e)}
                if args.from_tailor_tab:
                    client.update_manual_jd_tailor_result(
                        url=url,
                        status="EVAL_FAILED",
                        tailored_yaml="",
                        error=str(e),
                        last_processed=now,
                    )
                print(json.dumps(line, ensure_ascii=False) if args.json else f"  EVAL ERROR: {e}")
                continue
            try:
                score = int(eval_out.get("score", 0))
            except (TypeError, ValueError):
                score = 0
            ev_rec = str(eval_out.get("recommended_resume") or "").strip()
            rec_for_tailor = ev_rec or sheet_rec

        job_data = {
            "url": url,
            "Job Link": url,
            "description": jd_text,
            "recommended_resume": rec_for_tailor,
        }
        force = skip_eval
        run_started = time.time()
        path_yaml = tailor.process_job(
            job_data,
            score,
            force_tailor=force,
            skip_validation=args.skip_tailor_validation,
        )
        generated, artifact_msg = _resume_artifact_state(path_yaml, run_started_ts=run_started)
        vv = ""
        vr = ""
        ts = ""
        gs = ""
        use_resume = ""
        if validate_variants and path_yaml and jd_text:
            vv, vr, ts, gs, use_resume = _compare_tailored_vs_generic(
                tailor=tailor,
                path_yaml=path_yaml,
                jd_text=jd_text,
                recommended_resume=rec_for_tailor,
            )

        if args.skip_tailor_validation:
            status = "TAILORED_YAML_ONLY" if path_yaml else "TAILOR_FAILED"
            err_text = "" if path_yaml else (artifact_msg or "Tailoring did not produce YAML.")
        else:
            status = "RESUME_GENERATED" if generated else "TAILOR_FAILED"
            err_text = "" if generated else artifact_msg
        if args.from_tailor_tab:
            client.update_manual_jd_tailor_result(
                url=url,
                status=status,
                tailored_yaml=path_yaml or "",
                error=err_text,
                last_processed=now,
                validation_verdict=vv,
                validation_reason=vr,
                tailored_score=ts,
                generic_score=gs,
                use_resume=use_resume,
            )

        if args.json:
            out = {
                "url": url,
                "jd_source": jd_msg,
                "tailored_yaml": path_yaml,
                "evaluation_skipped": skip_eval,
                "recommended_resume_used": rec_for_tailor,
                "tailor_validation_skipped": args.skip_tailor_validation,
                "sheet_status": status,
                "validation_verdict": vv,
                "tailored_score": ts,
                "generic_score": gs,
                "use_resume": use_resume,
            }
            if err_text:
                out["error"] = err_text
            if eval_out is not None:
                out["evaluation"] = eval_out
            print(json.dumps(out, ensure_ascii=False))
        else:
            print(f"\n{'=' * 72}\n{url}\nJD: {jd_msg}")
            if rec_for_tailor:
                print(f"Recommended resume context: {rec_for_tailor}")
            if eval_out is not None:
                print(f"Score: {eval_out.get('score')} | {eval_out.get('verdict')}")
            if args.skip_tailor_validation:
                print("Tailor QA: skipped (YAML-only mode)")
            print(f"Sheet status: {status}")
            if err_text:
                print(f"Sheet error: {err_text}")
            if vv:
                print(f"Variant validation: {vv} (tailored={ts}, generic={gs}) -> use {use_resume}")
            print(f"Tailored YAML: {path_yaml}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
