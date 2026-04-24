#!/usr/bin/env python3
"""
Fetch JDs into jd_cache, optionally run JobEvaluator, then TailorAgent for each URL.

Usage (repo root):
  python3 scripts/tools/tailor_from_urls.py "https://..." "https://..."
  python3 scripts/tools/tailor_from_urls.py --file urls.txt
  # Default: tailor-only (no job-fit LLM). Use --also-eval to run evaluate_single_job first.
  python3 scripts/tools/tailor_from_urls.py --also-eval "https://..."
  # Manual_JD_Tailor: B = job URLs; 'Recommended Resume' column (auto-added after F on old tabs) = optional hint
  # Variant validation uses JobEvaluator content judge (2 LLM calls per row: tailored vs generic YAML vs JD).
  python3 scripts/tools/tailor_from_urls.py --from-tailor-tab
  # Skip TailorAgent QA/generate_resume; produce YAML only
  python3 scripts/tools/tailor_from_urls.py --from-tailor-tab --ensure-tailor-tab --skip-tailor-validation
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
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


def resume_output_path_from_tailored_yaml(path_yaml: str | None) -> str:
    """Absolute path to generated PDF, or .tex if PDF missing, else empty."""
    if not path_yaml or not os.path.isfile(path_yaml):
        return ""
    try:
        with open(path_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        meta = data.get("meta") if isinstance(data, dict) else {}
        rel_tex = str((meta or {}).get("filename") or "").strip()
        if not rel_tex:
            return ""
        resume_root = os.path.join(PROJECT_ROOT, "core_agents", "resume_agent")
        tex_path = os.path.normpath(os.path.join(resume_root, rel_tex))
        pdf_path = os.path.splitext(tex_path)[0] + ".pdf"
        if os.path.isfile(pdf_path):
            return pdf_path
        if os.path.isfile(tex_path):
            return tex_path
        return ""
    except Exception:
        return ""


def _resume_artifact_state(path_yaml: str | None, *, run_started_ts: float) -> tuple[bool, str]:
    """
    Returns (resume_generated, message).
    """
    if not path_yaml:
        return False, "Tailoring returned no YAML path."
    if not os.path.isfile(path_yaml):
        return False, "Tailored YAML not found on disk."
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


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _variant_sheet_score(res: dict) -> tuple[int, str]:
    """
    Ordering uses role_judge_score when the content judge succeeded; otherwise static ATS match %.
    Sheet shows integer judge score, or ATS-only when the LLM judge did not return JSON.
    """
    if res.get("judge_engine") == "OK":
        v = int(res.get("role_judge_score") or 0)
        return v, str(v)
    ap = int(res.get("ats_match_pct") or 0)
    return ap, f"{ap} (ATS-only)"


def _compare_tailored_vs_generic(
    *,
    evaluator: JobEvaluator,
    tailor: TailorAgent,
    path_yaml: str | None,
    jd_text: str,
    recommended_resume: str,
) -> tuple[str, str, str, str, str]:
    """
    Returns (verdict, reason, tailored_score, generic_score, use_resume).
    Scores come from JobEvaluator.judge_resume_yaml_against_jd (pillars + ATS overlay + LLM judge).
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

    t_res = evaluator.judge_resume_yaml_against_jd(jd_text, tailored_text)
    g_res = evaluator.judge_resume_yaml_against_jd(jd_text, generic_text)
    t_val, t_disp = _variant_sheet_score(t_res)
    g_val, g_disp = _variant_sheet_score(g_res)
    diff = t_val - g_val
    if diff > 0:
        verdict = "TAILORED_BETTER"
        use_resume = "TAILORED"
        reason = (
            f"Content judge: tailored {t_disp} vs generic {g_disp} (ordering {t_val} vs {g_val})."
        )
    elif diff < 0:
        verdict = "GENERIC_BETTER"
        use_resume = "GENERIC_RECOMMENDED"
        reason = (
            f"Content judge: generic {g_disp} vs tailored {t_disp} (ordering {g_val} vs {t_val})."
        )
    else:
        verdict = "TIE"
        use_resume = "TAILORED"
        reason = f"Content judge tie at {t_val} ({t_disp} vs {g_disp}); defaulting to tailored resume."
    notes: list[str] = []
    tn = (t_res.get("role_judge_notes") or "").strip()
    gn = (g_res.get("role_judge_notes") or "").strip()
    if tn:
        notes.append(f"Tailored: {tn[:160]}")
    if gn:
        notes.append(f"Generic: {gn[:160]}")
    if notes:
        reason = reason + " " + " ".join(notes)
    return (verdict, reason, t_disp, g_disp, use_resume)


def tailored_yaml_path_for_job_url(tailor: TailorAgent, url: str) -> str:
    """Absolute path to `JD_<stem>.yaml` for a canonical job URL."""
    stem = tailor._tailor_output_stem({"url": url, "Job Link": url})  # pylint: disable=protected-access
    return os.path.join(tailor.base_dir, "data", tailor._profile, "tailored", f"JD_{stem}.yaml")  # pylint: disable=protected-access


def compare_tailored_vs_generic_for_job(
    tailor: TailorAgent,
    url: str,
    jd_text: str,
    recommended_resume: str,
    evaluator: JobEvaluator | None = None,
) -> tuple[str, str, str, str, str]:
    """Public helper for backfill / tooling: same scoring as post-tailor validation."""
    ev = evaluator or JobEvaluator()
    return _compare_tailored_vs_generic(
        evaluator=ev,
        tailor=tailor,
        path_yaml=tailored_yaml_path_for_job_url(tailor, url),
        jd_text=jd_text,
        recommended_resume=recommended_resume,
    )


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
                    resume_path="",
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
                        resume_path="",
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
                evaluator=evaluator,
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
        resume_path = resume_output_path_from_tailored_yaml(path_yaml)
        if args.from_tailor_tab:
            client.update_manual_jd_tailor_result(
                url=url,
                status=status,
                resume_path=resume_path,
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
                "resume_pdf": resume_path,
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
            if resume_path:
                print(f"Resume output: {resume_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
