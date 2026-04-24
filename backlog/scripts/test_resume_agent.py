import asyncio
import os
import sys

from dotenv import load_dotenv
import os

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

# Load environment explicitly from project root
load_dotenv(os.path.join(project_root, '.env'))

from src.agents.resume_agent import ResumeAgent

async def test_tailoring():
    # 0. Load environment
    load_dotenv()
    
    # 1. Setup
    jd_text = """
    Technical Product Manager (AI/ML)
    We are looking for someone to lead the development of multi-agent AI ecosystems. 
    Required: 
    - Experience with Python, LangGraph, and FastAPI.
    - Proven track record of scaling AI products.
    - Strong background in Agile and Scrum methodologies.
    """
    
    output_tex = os.path.join(
        project_root,
        "core_agents/resume_agent/Resume_Building/Abhishek/Generated/test_tailored_resume.tex",
    )
    os.makedirs(os.path.dirname(output_tex), exist_ok=True)
    
    print("🚀 Starting Resume Tailoring Test...")
    api_key = os.getenv("GEMINI_API_KEY")
    agent = ResumeAgent(master_context_path="data/profiles/master_context.yaml")
    # Pass key explicitly if needed or handle it in agent
    if api_key:
        agent.llm.gemini_key = api_key
    
    # 2. Tailor
    path = await agent.tailor_resume(jd_text, output_tex, compile=True)
    
    print(f"\n✅ Tailoring complete! File saved at: {path}")
    
    if path.endswith(".pdf"):
        print("🎉 PDF generated successfully.")
    else:
        print("⚠ PDF generation failed or skipped.")

if __name__ == "__main__":
    asyncio.run(test_tailoring())
