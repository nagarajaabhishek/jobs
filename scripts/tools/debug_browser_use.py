import os
import sys
import asyncio
import traceback
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from browser_use import Agent
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    print("Dependencies missing.")
    sys.exit(1)

async def debug_run():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY missing.")
        return

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    
    # Apply the previous patch
    llm.__dict__['provider'] = 'google'
    
    print(f"DEBUG: llm.provider = {getattr(llm, 'provider', 'N/A')}")
    print(f"DEBUG: llm.ainvoke type = {type(llm.ainvoke)}")
    
    agent = Agent(
        task="Go to google.com and search for 'hello'",
        llm=llm
    )
    
    try:
        print("DEBUG: Starting agent.run()...")
        await agent.run(max_steps=1)
    except Exception:
        print("\n--- 🛑 TRACEBACK START 🛑 ---")
        traceback.print_exc()
        print("--- 🛑 TRACEBACK END 🛑 ---\n")

if __name__ == "__main__":
    asyncio.run(debug_run())
