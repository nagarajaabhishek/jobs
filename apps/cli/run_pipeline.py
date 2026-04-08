import sys
import os
import uuid
import logging

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_agents.sourcing_agent.agent import SourcingAgent
from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient
from apps.cli.legacy.core.workflow_registry import WorkflowRegistry
from apps.cli.legacy.core.config import get_cycle_config, get_digest_config, get_sourcing_config
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

    if cycle_cfg.get("automation_hooks_enabled"):
        logger.info(
            "automation_hooks_enabled is true — no auto-apply is performed; manual approval required per policy."
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


def run_full_pipeline():
    cycle_id = str(uuid.uuid4())[:8]
    logger.info("Starting daily pipeline cycle_id=%s", cycle_id)
    print("\n--- Starting Target-Driven Interleaved Pipeline ---\n")

    cfg = get_sourcing_config()
    os.environ["PIPELINE_CYCLE_ID"] = cycle_id
    _preflight_checks(cfg)
    queries = cfg.get("queries", [])
    locations = cfg.get("locations", [])
    results_wanted = cfg.get("results_wanted", 50) # Legacy total target
    max_workers = cfg.get("max_workers", 4)

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

    print(f"\nTarget Goal: Find at least 50 High-Priority ('Must Apply') matches.")
    total_must_applies = 0
    iteration = 1
    
    # SOP: 10/10 Interleaved Loop
    while total_must_applies < 50:
        print(f"\n--- Iteration {iteration} (Target: 50 | Current: {total_must_applies}) ---")
        
        # Grab a single query round-robin to keep the loop tight
        current_query = queries[(iteration - 1) % len(queries)]
        
        # Override the target size to only source a small batch per iteration
        batch_size = 15 
        iter_locations = {loc: batch_size for loc in locations.keys()}

        print(f"Sourcing next batch (~{batch_size} jobs) for '{current_query}'...")
        sourcing_agent.scrape_jobspy_parallel(
            queries=[current_query], 
            locations=iter_locations, 
            max_workers=max_workers,
            use_ai_filter=use_ai_filter
        )
        
        # 2. Evaluate all NEW jobs immediately
        print("Evaluating current batch...")
        high_scoring_jobs = evaluator.evaluate_all(mode="NEW", limit=batch_size * 2, cycle_id=cycle_id) or []
        batch_matches = len(high_scoring_jobs)
        total_must_applies += batch_matches
        
        # 3. Tailor High-Scoring Jobs and record resume artifacts for human review.
        if high_scoring_jobs:
            print(f"\n--- Tailoring Phase: Processing {batch_matches} high-conviction jobs ---")
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

        print(f"Iteration {iteration} Summary: Found and tailored {batch_matches} high-priority matches.")
        
        if total_must_applies >= 50:
            print(f"\n🎯 Goal Achieved! Found {total_must_applies} 'Must Apply' jobs.")
            break
            
        if iteration > 10: # Safety break to avoid infinite loops
            print("\n⚠ Safety limit reached (10 iterations). Stopping.")
            break
            
        iteration += 1

    # Step 3: Final Specialized Sources (One-off)
    print("\n--- Running Specialized Community Sources ---")
    sourcing_agent.scrape_community_sources_once(queries=queries)
    evaluator.evaluate_all(mode="NEW", cycle_id=cycle_id)

    print("\n--- Final Sorting ---")
    client.sort_daily_jobs()

    print("\n--- Cycle hooks (digest / feedback) ---")
    _run_cycle_hooks(cycle_id)

    print(f"\n--- Pipeline Execution Complete. Total High-Priority Found: {total_must_applies} ---")


if __name__ == "__main__":
    run_full_pipeline()
