import os
import sys
import logging
import json

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from google import adk # type: ignore
    from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent # type: ignore
except ImportError:
    logging.warning("ADK not installed. Running in prototype/documentation mode.")

from src.agents.sourcing_agent import SourcingAgent # type: ignore
from src.agents.evaluate_jobs import JobEvaluator # type: ignore
from src.core.llm_router import LLMRouter # type: ignore

def sourcing_tool(query: str, location: str = "United States"):
    """
    Real tool for sourcing jobs. Returns a JSON list of job URLs.
    """
    sourcing = SourcingAgent()
    logging.info(f"ADK Sourcing Tool: Searching for {query}")
    # We modify source_batch to return the direct list of job dictionaries
    jobs = sourcing.source_batch(query=query, location=location)
    urls = [job.get('job_url') for job in jobs if job.get('job_url')]
    
    # Returning JSON string so the LLM can parse the list of URLs
    return json.dumps({
        "status": "success",
        "count": len(urls),
        "urls": urls
    })

def evaluation_tool(url: str):
    """
    Real tool for evaluating a specific job.
    """
    evaluator = JobEvaluator()
    logging.info(f"ADK Evaluation Tool: Scoring {url}")
    result = evaluator.evaluate_single_job(url)
    return json.dumps({
        "url": url,
        "verdict": result.get('verdict', 'UNKNOWN'),
        "score": result.get('score', 0)
    })

def create_job_pipeline_agent():
    """
    Creates an ADK-based multi-agent pipeline with real tools and state handoff.
    """
    
    # 1. Sourcing Agent
    sourcing_agent = LlmAgent(
        name="JobSourcingAgent",
        instruction="""
        Use 'sourcing_tool' to find jobs. 
        Return the JSON result exactly so the Chief Agent can see the URLs.
        """,
        tools=[sourcing_tool]
    )
    
    # 2. Evaluation Agent
    evaluator_agent = LlmAgent(
        name="JobEvaluatorAgent",
        instruction="""
        Ingest a list of URLs. 
        For EVERY URL provided, call 'evaluation_tool'.
        Provide a summary table of scores at the end.
        """,
        tools=[evaluation_tool]
    )
    
    # 3. Chief Orchestrator
    router_agent = LlmAgent(
        name="ChiefJobAgent",
        instruction="""
        You are the Chief Coordinator.
        1. Ask 'JobSourcingAgent' to find jobs for the user's request.
        2. Extract the list of URLs from the sourcing response.
        3. Pass those URLs to 'JobEvaluatorAgent' for scoring.
        4. Present the final MUST APPLY roles to the user.
        """
    )
    
    # 4. Pipeline
    pipeline = SequentialAgent(
        name="FullJobPipeline",
        sub_agents=[sourcing_agent, evaluator_agent, router_agent]
    )
    
    return pipeline

if __name__ == "__main__":
    print("--- ADK Multi-Agent Pipeline (Live Production Run) ---")
    
    # 1. Initialize Pipeline
    pipeline = create_job_pipeline_agent()
    
    # 2. Define Production Query
    # Target: Texas (Resident) and Dubai (Strategic Expansion)
    # Focus: Associate / Entry-level roles
    prod_query = (
        "Search for Product Manager (TPM), Product Owner, and Business Analyst roles. "
        "Focus on Texas (Dallas/Austin/Arlington) and Dubai/UAE. "
        "Prioritize associate and entry-level positions. "
        "Evaluate ALL found URLs for fit and provide reasoning in Google Sheets."
    )
    
    print(f"\n🚀 Starting Production Run with query:\n\"{prod_query}\"")
    
    try:
        # Note: pipeline.run will trigger the agent loop
        pipeline.run(input=prod_query)
        print("\n✅ Production Run Completed.")
    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}")
        logging.error(f"ADK Run Failed: {e}", exc_info=True)
