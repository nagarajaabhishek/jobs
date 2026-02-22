import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.agents.sourcing_agent import SourcingAgent
from src.agents.evaluate_jobs import JobEvaluator
from src.core.google_sheets_client import GoogleSheetsClient
from src.core.workflow_registry import WorkflowRegistry
from src.core.config import get_sourcing_config


def run_full_pipeline():
    print("\n--- Starting Job Automation Pipeline ---\n")

    cfg = get_sourcing_config()
    queries = cfg.get("queries", [])
    locations = cfg.get("locations", [])
    results_wanted = cfg.get("results_wanted", 50)
    max_workers = cfg.get("max_workers", 4)

    client = GoogleSheetsClient()
    sourcing_agent = SourcingAgent(client)
    wf = WorkflowRegistry()

    # AI Sourcing Flags
    expand_ai = cfg.get("expand_ai_queries", False)
    use_ai_filter = cfg.get("use_ai_filter", False)

    # Step 1: Prerequisites Check (Implicit)
    wf.log_step("job_pipeline.md", 1)

    # Step 2: Run Sourcing & Evaluation
    wf.log_step("job_pipeline.md", 2)

    # Expand queries if enabled
    if expand_ai:
        queries = sourcing_agent.expand_queries(queries)

    sourcing_agent.scrape_community_sources_once(queries=queries)

    print("\n--- JobSpy (parallel) ---")
    raw_jobs = sourcing_agent.scrape_jobspy_parallel(
        queries=queries, locations=locations, max_workers=max_workers,
    )
    
    # Custom call to normalize_and_save with AI filter
    sourcing_agent.normalize_and_save(raw_jobs, use_ai_filter=use_ai_filter)

    print("\n--- Evaluation Phase (single pass) ---")
    evaluator = JobEvaluator()
    evaluator.evaluate_all()

    # Step 3: Verify
    wf.log_step("job_pipeline.md", 3)

    print("\n--- Final Sorting ---")
    client.sort_daily_jobs()
    
    print("\n--- Pipeline Execution Complete ---")


if __name__ == "__main__":
    run_full_pipeline()
