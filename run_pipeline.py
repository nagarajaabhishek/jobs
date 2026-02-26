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
    print("\n--- Starting Target-Driven Interleaved Pipeline ---\n")

    cfg = get_sourcing_config()
    queries = cfg.get("queries", [])
    locations = cfg.get("locations", [])
    results_wanted = cfg.get("results_wanted", 50) # Legacy total target
    max_workers = cfg.get("max_workers", 4)

    client = GoogleSheetsClient()
    sourcing_agent = SourcingAgent(client)
    evaluator = JobEvaluator()
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
        batch_matches = evaluator.evaluate_all(mode="NEW", limit=batch_size * 2)
        total_must_applies += batch_matches
        
        print(f"Iteration {iteration} Summary: Found {batch_matches} high-priority matches.")
        
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
    evaluator.evaluate_all(mode="NEW")

    print("\n--- Final Sorting ---")
    client.sort_daily_jobs()
    
    print(f"\n--- Pipeline Execution Complete. Total High-Priority Found: {total_must_applies} ---")


if __name__ == "__main__":
    run_full_pipeline()
