import asyncio
import os
import sys
from pathlib import Path
from typing import Dict

# Ensure project root is in path
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from src.agents.apply_agent import ApplyAgent # type: ignore

async def dry_run_apply():
    """
    Performs a non-submitting dry run of the ApplyAgent on a demo job board.
    """
    # Use a dummy URL for the test - browser-use will still try to navigate
    # and identifying the form structure.
    test_url = "https://www.google.com/search?q=demo+job+application+page" # Just a starting point
    
    # In a real test, you'd find a specific "Apply" page from one of your MUST APPLY roles.
    
    user_context = {
        "first_name": "Abhishek",
        "last_name": "Nagaraja",
        "email": "abhishek.n@example.com", # Added for better form filling
        "linkedin_url": "https://linkedin.com/in/nagarajaabhishek",
        "portfolio_url": "https://abhisheknagaraja.com"
    }
    
    resume_path = str(
        _REPO_ROOT
        / "core_agents/resume_agent/Resume_Building/Abhishek/Master/Abhishek_Nagaraja_Master_Resume.pdf"
    )
    if not os.path.isfile(resume_path):
        raise FileNotFoundError(
            f"Master resume not found at {resume_path}. "
            "Build it from the .tex in that folder or see data/resumes/README.md."
        )

    print("\n--- 🤖 Starting ApplyAgent Dry Run ---")
    print("Goal: Observe the browser navigating and identifying form fields.")
    print("Safety Check: The agent is instructed to STOP before clicking Submit.")
    
    agent = ApplyAgent()
    
    # MISSION: Navigate to a job portal and identify fields
    # For this test, let's try a real but safe URL like a sample Ashby board if we can find one, 
    # or just let it roam a search result to show it can handle the browser.
    
    try:
        await agent.apply_to_job(
            url="https://jobs.lever.co/google", # Example Lever page
            resume_path=resume_path,
            context_details=user_context
        )
    except Exception as e:
        print(f"❌ Error during dry run: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(dry_run_apply())
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
