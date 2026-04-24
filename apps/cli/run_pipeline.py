import sys
import os
import uuid
import logging

from gspread.exceptions import APIError

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_agents.sourcing_agent.agent import SourcingAgent
from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, SheetsReadError
from apps.cli.legacy.core.workflow_registry import WorkflowRegistry
from apps.cli.legacy.core.config import (
    get_cycle_config,
    get_digest_config,
    get_evaluation_config,
    get_sourcing_config,
)
from apps.cli.legacy.core.preflight import run_cycle_preflight
from core_agents.resume_agent.tailor import TailorAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("job_pipeline")


def _import_tool_module(name: str):
    import importlib.util

    path = os.path.join(PROJECT_ROOT, "apps", "cli", "scripts", "tools", f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tool module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_cycle_hooks(cycle_id: str):
    """Optional digest generation and feedback ingestion (config: cycle.*)."""
    os.environ["PIPELINE_CYCLE_ID"] = cycle_id
    cycle_cfg = get_cycle_config()
    digest_cfg = get_digest_config()

    if cycle_cfg.get("run_feedback_ingest"):
        try:
            ingest = _import_tool_module("ingest_feedback")
            ingest.ingest_sheet_rows(dry_run=False)
        except Exception as e:
            logger.warning("Feedback ingest failed: %s", e)

    if cycle_cfg.get("run_digest_after_pipeline", True) and digest_cfg.get("enabled", True):
        try:
            digest_mod = _import_tool_module("build_job_digest")
            top_n = int(digest_cfg.get("top_n", 20))
            digest_mod.build_digest(top_n=top_n, update_sheet=True, dry_run=False)
        except Exception as e:
            logger.warning("Digest build failed: %s", e)

    if cycle_cfg.get("run_career_strategy"):
        try:
            cs_mod = _import_tool_module("build_career_strategy")
            cs_mod.build_career_strategy()
        except Exception as e:
            logger.warning("Career strategy build failed: %s", e)

    if cycle_cfg.get("run_filter_learning"):
        try:
            learn_mod = _import_tool_module("learn_sourcing_filters_from_sheet")
            learn_mod.learn_from_sheet(
                out=str(cycle_cfg.get("filter_learning_output", "data/sourcing_learned_title_blocks.yaml")),
                neg_max_score=int(cycle_cfg.get("filter_learning_neg_max_score", 65)),
                pos_min_score=int(cycle_cfg.get("filter_learning_pos_min_score", 80)),
                min_neg_count=int(cycle_cfg.get("filter_learning_min_neg_count", 3)),
                min_lift=float(cycle_cfg.get("filter_learning_min_lift", 2.0)),
                max_phrases=int(cycle_cfg.get("filter_learning_max_phrases", 100)),
                dry_run=bool(cycle_cfg.get("filter_learning_dry_run", False)),
            )
        except Exception as e:
            logger.warning("Filter learning failed: %s", e)

    if cycle_cfg.get("run_sourcing_hints"):
        try:
            hints_mod = _import_tool_module("suggest_sourcing_sources")
            out = str(cycle_cfg.get("sourcing_hints_output", "data/sourcing_hints.yaml"))
            hints_mod.run_sourcing_hints(
                project_root=PROJECT_ROOT,
                recent_tabs=int(cycle_cfg.get("sourcing_hints_recent_tabs", 21)),
                tab_filter=str(cycle_cfg.get("sourcing_hints_tab_filter", "") or "").strip(),
                thr_70=float(cycle_cfg.get("sourcing_hints_thr_70", 70.0)),
                thr_80=float(cycle_cfg.get("sourcing_hints_thr_80", 80.0)),
                min_rows_per_source=int(cycle_cfg.get("sourcing_hints_min_rows_per_source", 5)),
                top_sources=int(cycle_cfg.get("sourcing_hints_top_sources", 25)),
                top_companies=int(cycle_cfg.get("sourcing_hints_top_companies", 40)),
                output_path=out,
                quiet=bool(cycle_cfg.get("sourcing_hints_quiet", True)),
            )
            logger.info("Sourcing hints written to %s", out)
        except Exception as e:
            logger.warning("Sourcing hints failed: %s", e)

    if cycle_cfg.get("automation_hooks_enabled"):
        logger.info(
            "automation_hooks_enabled is true — no auto-apply is performed; manual approval required per policy."
        )


def _tailor_high_conviction_rows(client, tailor_agent, high_scoring_jobs):
    """Generate resume artifacts for evaluator-returned high-conviction jobs."""
    if not high_scoring_jobs:
        return
    n = len(high_scoring_jobs)
    print(f"\n--- Tailoring Phase: Processing {n} high-conviction job(s) ---")
    for job_data in high_scoring_jobs:
        resume_path = tailor_agent.process_job(
            job_data, job_data.get("evaluation_score", 90)
        )
        if resume_path:
            ws = job_data.get("_worksheet")
            row_index = job_data.get("_row_index")
            if ws is not None and row_index is not None:
                client.update_resume_for_row(
                    ws,
                    int(row_index),
                    resume_path=resume_path,
                    resume_status="GENERATED_PENDING_REVIEW",
                    reviewer_notes="",
                )


def _preflight_checks(cfg):
    # Load .env if python-dotenv is installed (avoid surprises in CLI runs).
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    queries = cfg.get("queries", [])
    if not queries:
        raise RuntimeError("Preflight failed: sourcing queries are empty in config/pipeline.yaml.")

    res = run_cycle_preflight(project_root=PROJECT_ROOT)
    if not res.ok:
        raise RuntimeError("Preflight failed:\n- " + "\n- ".join(res.errors))
    logger.info(
        "Preflight OK (profiles + credentials + evaluation provider prerequisites). "
        "warnings=%s",
        len(res.warnings),
    )


def _count_eval_backlog(client, sample_limit: int = 5000):
    """Return counts for today's NEW / NEEDS_REVIEW / LLM_FAILED buckets."""
    new_jobs, _ = client.get_new_jobs(limit=sample_limit)
    needs_review_jobs, _ = client.get_needs_review_jobs(limit=sample_limit)
    llm_failed_jobs, _ = client.get_llm_failed_jobs(limit=sample_limit)
    return {
        "NEW": len(new_jobs or []),
        "NEEDS_REVIEW": len(needs_review_jobs or []),
        "LLM_FAILED": len(llm_failed_jobs or []),
    }


def _is_sheets_read_failure(exc: Exception) -> bool:
    if isinstance(exc, SheetsReadError):
        return True
    if isinstance(exc, APIError):
        try:
            if getattr(exc.response, "status_code", None) == 429:
                return True
        except Exception:
            pass
    msg = str(exc).lower()
    return "429" in msg and "quota" in msg


def _read_phase_gate_metrics(client, target_score_min: float):
    """Return (backlog_counts, target_hits) or re-raise on Sheets failure after client retries."""
    final_counts = _count_eval_backlog(client)
    final_target_hits = client.count_evaluated_jobs_min_score(min_score=target_score_min)
    return final_counts, final_target_hits


def run_full_pipeline():
    cycle_id = str(uuid.uuid4())[:8]
    logger.info("Starting daily pipeline cycle_id=%s", cycle_id)
    print("\n--- Starting Target-Driven Interleaved Pipeline ---\n")

    cfg = get_sourcing_config()
    os.environ["PIPELINE_CYCLE_ID"] = cycle_id
    _preflight_checks(cfg)
    queries = cfg.get("queries", [])
    locations = cfg.get("locations", {})
    target_count = int(cfg.get("target_count", cfg.get("results_wanted", 50)))
    target_score_min = float(cfg.get("target_score_min", 80))
    max_workers = cfg.get("max_workers", 4)
    base_batch_size = int(cfg.get("interleaved_batch_size", 15) or 15)
    max_batch_size = int(cfg.get("interleaved_max_batch_size", 40) or 40)
    stall_round_threshold = int(cfg.get("interleaved_stall_threshold", 2) or 2)

    if isinstance(locations, dict):
        normalized_locations = {str(k): int(v) for k, v in locations.items() if str(k).strip()}
    elif isinstance(locations, list):
        normalized_locations = {str(loc): base_batch_size for loc in locations if str(loc).strip()}
    else:
        normalized_locations = {}
    if not normalized_locations:
        # Keep one stable fallback so the sourcing loop never crashes on malformed config.
        normalized_locations = {"United States": base_batch_size}

    client = GoogleSheetsClient()
    sourcing_agent = SourcingAgent(client)
    evaluator = JobEvaluator()
    tailor_agent = TailorAgent()
    wf = WorkflowRegistry()

    # AI Sourcing Flags
    expand_ai = cfg.get("expand_ai_queries", False)
    use_ai_filter = cfg.get("use_ai_filter", False)

    # Step 1: Prerequisites Check (Implicit)
    wf.log_step("job_pipeline.md", 1)

    # Expand queries if enabled
    if expand_ai:
        queries = sourcing_agent.expand_queries(queries)

    eval_cfg = get_evaluation_config()

    # Phase -1: Drain retryable evaluation backlog before sourcing new jobs.
    if eval_cfg.get("run_needs_review_sweep") or eval_cfg.get("run_llm_failed_sweep"):
        print("\n--- Pre-cycle Sweep: drain NEEDS_REVIEW / LLM_FAILED before new sourcing ---")
        if eval_cfg.get("run_needs_review_sweep"):
            nr_limit = int(eval_cfg.get("needs_review_sweep_limit", 200))
            print(f"  Pre-sweep NEEDS_REVIEW (limit={nr_limit})...")
            evaluator.evaluate_all(mode="NEEDS_REVIEW", limit=nr_limit, cycle_id=cycle_id)
        if eval_cfg.get("run_llm_failed_sweep"):
            lf_limit = int(eval_cfg.get("llm_failed_sweep_limit", 200))
            print(f"  Pre-sweep LLM_FAILED (limit={lf_limit})...")
            evaluator.evaluate_all(mode="LLM_FAILED", limit=lf_limit, cycle_id=cycle_id)

    total_target_hits = client.count_evaluated_jobs_min_score(min_score=target_score_min)
    jobright_ran_first = False
    if cfg.get("run_jobright_first", True):
        print("\n--- Phase 0: Jobright (GitHub READMEs) — first ---")
        sourcing_agent.scrape_jobright_github_only(use_ai_filter=use_ai_filter)
        jobright_ran_first = True
        jr_limit = int(eval_cfg.get("limit", 50))
        jobright_waves = int(cfg.get("jobright_eval_max_waves", 1) or 1)
        jobright_waves = max(1, jobright_waves)
        print(
            f"Evaluating NEW jobs after Jobright (limit={jr_limit} per wave, "
            f"max_waves={jobright_waves})..."
        )
        for wave in range(1, jobright_waves + 1):
            print(f"  Jobright eval wave {wave}/{jobright_waves}...")
            jr_high = evaluator.evaluate_all(mode="NEW", limit=jr_limit, cycle_id=cycle_id) or []
            _tailor_high_conviction_rows(client, tailor_agent, jr_high)
            total_target_hits = client.count_evaluated_jobs_min_score(min_score=target_score_min)
            if total_target_hits >= target_count:
                break

    print(
        f"\nTarget Goal: Find at least {target_count} evaluated jobs with Apply Score >= {target_score_min:.0f}."
    )
    iteration = 1
    interleaved_max = int(cfg.get("interleaved_max_iterations", 10) or 10)
    interleaved_max = max(1, interleaved_max)
    adaptive_batch_size = max(5, base_batch_size)
    stalled_rounds = 0
    community_escalation_used = False

    # SOP: interleaved JobSpy loop (max iterations configurable)
    while total_target_hits < target_count:
        print(f"\n--- Iteration {iteration} (Target: {target_count} | Current: {total_target_hits}) ---")
        
        # Grab a single query round-robin to keep the loop tight
        current_query = queries[(iteration - 1) % len(queries)]
        
        # Adaptive batch sizing: when iterations produce no new high-score rows, increase sourcing depth.
        batch_size = min(max_batch_size, adaptive_batch_size)
        iter_locations = {loc: max(batch_size, int(target)) for loc, target in normalized_locations.items()}

        print(f"Sourcing next batch (~{batch_size} jobs) for '{current_query}'...")
        sourcing_agent.scrape_jobspy_parallel(
            queries=[current_query], 
            locations=iter_locations, 
            max_workers=max_workers,
            use_ai_filter=use_ai_filter
        )
        
        # 2. Evaluate all NEW jobs immediately
        print("Evaluating current batch...")
        prev_hits = total_target_hits
        high_scoring_jobs = evaluator.evaluate_all(
            mode="NEW",
            limit=max(batch_size * 2, int(eval_cfg.get("limit", 50))),
            cycle_id=cycle_id,
        ) or []
        total_target_hits = client.count_evaluated_jobs_min_score(min_score=target_score_min)
        batch_matches = max(0, total_target_hits - prev_hits)
        
        _tailor_high_conviction_rows(client, tailor_agent, high_scoring_jobs)

        print(
            f"Iteration {iteration} Summary: +{batch_matches} rows reached score >= {target_score_min:.0f} "
            f"(now {total_target_hits}/{target_count})."
        )

        if batch_matches <= 0:
            stalled_rounds += 1
            if stalled_rounds >= stall_round_threshold:
                next_batch = min(max_batch_size, adaptive_batch_size + 10)
                if next_batch != adaptive_batch_size:
                    print(
                        f"  ↗ No score progress for {stalled_rounds} rounds; "
                        f"increasing interleaved batch size {adaptive_batch_size} -> {next_batch}."
                    )
                    adaptive_batch_size = next_batch
        else:
            stalled_rounds = 0

        # One-time escalation: bring specialized sources earlier when JobSpy loop stalls.
        if (
            not community_escalation_used
            and stalled_rounds >= max(stall_round_threshold, 2)
            and total_target_hits < target_count
        ):
            print(
                "  ↗ Interleaved loop stalled; running specialized community sources early "
                "to widen sourcing coverage."
            )
            sourcing_agent.scrape_community_sources_once(
                queries=[current_query],
                skip_jobright=jobright_ran_first,
            )
            esc_high = evaluator.evaluate_all(
                mode="NEW",
                limit=max(int(eval_cfg.get("limit", 50)), batch_size * 2),
                cycle_id=cycle_id,
            ) or []
            _tailor_high_conviction_rows(client, tailor_agent, esc_high)
            total_target_hits = client.count_evaluated_jobs_min_score(min_score=target_score_min)
            community_escalation_used = True
        
        if total_target_hits >= target_count:
            print(
                f"\n🎯 Goal Achieved! Found {total_target_hits} evaluated jobs with score >= {target_score_min:.0f}."
            )
            break
            
        if iteration >= interleaved_max:
            print(f"\n⚠ Safety limit reached ({interleaved_max} iterations). Stopping.")
            break
            
        iteration += 1

    # Step 3: Final Specialized Sources (One-off)
    print("\n--- Running Specialized Community Sources ---")
    sourcing_agent.scrape_community_sources_once(queries=queries, skip_jobright=jobright_ran_first)
    comm_high = evaluator.evaluate_all(mode="NEW", cycle_id=cycle_id) or []
    _tailor_high_conviction_rows(client, tailor_agent, comm_high)

    # Optional: clean up retryable eval failures (NEEDS_REVIEW / LLM_FAILED) at end of cycle.
    if eval_cfg.get("run_needs_review_sweep"):
        nr_limit = int(eval_cfg.get("needs_review_sweep_limit", 200))
        print(f"\n--- Post-cycle Sweep: NEEDS_REVIEW (limit={nr_limit}) ---")
        evaluator.evaluate_all(mode="NEEDS_REVIEW", limit=nr_limit, cycle_id=cycle_id)
    if eval_cfg.get("run_llm_failed_sweep"):
        lf_limit = int(eval_cfg.get("llm_failed_sweep_limit", 200))
        print(f"\n--- Post-cycle Sweep: LLM_FAILED (limit={lf_limit}) ---")
        evaluator.evaluate_all(mode="LLM_FAILED", limit=lf_limit, cycle_id=cycle_id)

    # Optional strict mode: keep evaluating until today's tab has no NEW/NEEDS_REVIEW/LLM_FAILED rows.
    if eval_cfg.get("enforce_clean_sheet_before_finish"):
        clean_limit = int(eval_cfg.get("clean_sheet_pass_limit", eval_cfg.get("limit", 300)))
        clean_max_passes = int(eval_cfg.get("clean_sheet_max_passes", 6))
        print(
            f"\n--- Strict Cleanup Mode: draining NEW/NEEDS_REVIEW/LLM_FAILED "
            f"(max_passes={clean_max_passes}, per_pass_limit={clean_limit}) ---"
        )
        for p in range(1, clean_max_passes + 1):
            counts = _count_eval_backlog(client)
            new_n = counts["NEW"]
            nr_n = counts["NEEDS_REVIEW"]
            lf_n = counts["LLM_FAILED"]
            print(f"  Pass {p}: NEW={new_n}, NEEDS_REVIEW={nr_n}, LLM_FAILED={lf_n}")
            if new_n == 0 and nr_n == 0 and lf_n == 0:
                print("  ✅ Sheet is clean for today's tab.")
                break
            if new_n > 0:
                evaluator.evaluate_all(mode="NEW", limit=min(clean_limit, new_n), cycle_id=cycle_id)
            if nr_n > 0:
                evaluator.evaluate_all(mode="NEEDS_REVIEW", limit=min(clean_limit, nr_n), cycle_id=cycle_id)
            if lf_n > 0:
                evaluator.evaluate_all(mode="LLM_FAILED", limit=min(clean_limit, lf_n), cycle_id=cycle_id)
        else:
            counts = _count_eval_backlog(client)
            print(
                "  ⚠ Strict cleanup reached max passes with backlog remaining: "
                f"NEW={counts['NEW']}, NEEDS_REVIEW={counts['NEEDS_REVIEW']}, LLM_FAILED={counts['LLM_FAILED']}"
            )

    # End-of-pipeline phase gates.
    print("\n--- Phase Gates ---")
    gate_ok = True
    skip_gates_on_sheets = str(
        os.environ.get("PIPELINE_SKIP_TARGET_GATE_ON_SHEETS_ERROR", "")
    ).strip().lower() in ("1", "true", "yes")
    try:
        final_counts, final_target_hits = _read_phase_gate_metrics(client, target_score_min)
    except Exception as gate_read_err:
        if skip_gates_on_sheets and _is_sheets_read_failure(gate_read_err):
            print(
                f"  ⚠ Sheets read failed during phase gates ({gate_read_err!r}). "
                "Skipping target/clean-sheet gates (PIPELINE_SKIP_TARGET_GATE_ON_SHEETS_ERROR)."
            )
            final_counts = {"NEW": -1, "NEEDS_REVIEW": -1, "LLM_FAILED": -1}
            final_target_hits = -1
        else:
            raise
    else:
        print(
            f"  Gate: Score target >= {target_score_min:.0f} count {target_count} "
            f"(current={final_target_hits})"
        )
        if eval_cfg.get("require_target_count_before_finish") and final_target_hits < target_count:
            gate_ok = False
            print("  ❌ Target-count gate failed.")
        else:
            print("  ✅ Target-count gate passed.")

        print(
            "  Gate: Clean sheet NEW/NEEDS_REVIEW/LLM_FAILED "
            f"(current={final_counts['NEW']}/{final_counts['NEEDS_REVIEW']}/{final_counts['LLM_FAILED']})"
        )
        if eval_cfg.get("require_clean_sheet_before_finish") and any(
            final_counts[k] > 0 for k in ("NEW", "NEEDS_REVIEW", "LLM_FAILED")
        ):
            gate_ok = False
            print("  ❌ Clean-sheet gate failed.")
        else:
            print("  ✅ Clean-sheet gate passed.")

    if not gate_ok:
        raise RuntimeError("Pipeline phase gates failed. See gate output above.")

    print("\n--- Final Sorting ---")
    client.sort_daily_jobs()

    print("\n--- Cycle hooks (digest / feedback / sourcing hints) ---")
    _run_cycle_hooks(cycle_id)

    if final_target_hits >= 0:
        print(
            f"\n--- Pipeline Execution Complete. Total rows with score >= {target_score_min:.0f}: "
            f"{final_target_hits} ---"
        )
    else:
        print(
            f"\n--- Pipeline Execution Complete. Score >= {target_score_min:.0f} count unavailable "
            "(Sheets gate skipped). ---"
        )


if __name__ == "__main__":
    run_full_pipeline()
