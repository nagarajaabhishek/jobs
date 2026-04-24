import os
import sys
from pathlib import Path
import asyncio
import logging
from typing import Optional

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from browser_use import Agent # type: ignore
    from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
except ImportError:
    # Fallback placeholders for static analysis
    class Agent: 
        def __init__(self, *args, **kwargs): pass
        async def run(self): return "PROTOTYPE_MODE"
    class ChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs): pass
    logging.warning("browser-use or langchain-google-genai not installed. Running in prototype mode.")

class BrowserUseLLMWrapper:
    """
    Compatibility wrapper for browser-use + LangChain Google GenAI.
    Bypasses Pydantic validation issues in environments like Python 3.14.
    """
    def __init__(self, llm):
        self.llm = llm
        self.provider = 'google'
        # browser-use expects model_name for internal events/telemetry
        self.model_name = getattr(llm, 'model', 'gemini-1.5-flash')
        
    def __getattr__(self, name):
        return getattr(self.llm, name)
        
    async def ainvoke(self, *args, **kwargs):
        # Explicit delegation to bypass potential Pydantic __getattr__ traps
        return await self.llm.ainvoke(*args, **kwargs)

class ApplyAgent:
    """
    Experimental 'Last-Mile' agent that uses browser-automation to auto-fill job applications.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for the ApplyAgent.")
            
        # Initialize the LLM for browser guidance
        raw_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )
        
        # Wrap the LLM for browser-use compatibility
        self.llm = BrowserUseLLMWrapper(raw_llm)

    async def apply_to_job(self, url: str, resume_path: str, context_details: dict):
        """
        Navigates to the job URL and attempts to fill out the form.
        """
        # Ensure resume path is absolute
        abs_resume_path = os.path.abspath(resume_path)
        
        # Define the mission for the browser agent
        task = f"""
        MISSION: Navigate to the job application at {url} and fill it out accurately using the provided data.
        
        DATA:
        - First Name: {context_details.get('first_name')}
        - Last Name: {context_details.get('last_name')}
        - Full Name: {context_details.get('first_name')} {context_details.get('last_name')}
        - Email: {context_details.get('email', 'N/A')}
        - LinkedIn: {context_details.get('linkedin_url')}
        - Portfolio/Website: {context_details.get('portfolio_url')}
        - Resume File: {abs_resume_path}
        
        STEPS:
        1. Navigate to the URL.
        2. Identify the 'Apply' button or the application form.
        3. Fill in all contact information fields.
        4. Upload the resume file from the path: {abs_resume_path}
        5. If there are custom questions, answer them as best as possible using the data.
        6. CRITICAL: Once the form is filled but BEFORE clicking 'Submit' or 'Finish', STOP.
        7. Provide a summary of the filled fields and wait for human confirmation.
        """
        
        if Agent is type(None) or not hasattr(self, 'llm'):
            print("  ⚠ ApplyAgent is in prototype mode. browser-use is not fully configured.")
            return "PROTOTYPE_MODE"

        agent = Agent(
            task=task,
            llm=self.llm,
        )
        
        print(f"🚀 Starting Auto-Apply Agent flow for: {url}")
        result = await agent.run()
        return result

if __name__ == "__main__":
    # Prototype execution logic
    details = {
        "first_name": "Abhishek",
        "last_name": "Nagaraja",
        "linkedin_url": "https://linkedin.com/in/nagarajaabhishek",
        "portfolio_url": "https://abhisheknagaraja.com"
    }
    
    _repo_root = Path(__file__).resolve().parents[2]
    resume = str(
        _repo_root
        / "core_agents/resume_agent/Resume_Building/Abhishek/Master/Abhishek_Nagaraja_Master_Resume.pdf"
    )
    
    # agent = ApplyAgent()
    # asyncio.run(agent.apply_to_job("https://example-job-board.com/apply/123", resume, details))
    print("ApplyAgent Prototype Ready. Install 'browser-use' to activate.")
