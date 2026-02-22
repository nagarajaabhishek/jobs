from src.core.llm_router import LLMRouter
from src.agents.evaluate_jobs import JobEvaluator

import logging
logging.basicConfig(level=logging.ERROR)

evaluator = JobEvaluator()

print("--- Testing Ollama Configuration ---")
try:
    if evaluator.llm and getattr(evaluator.llm, "ollama_model", None):
        print(f"Ollama client configured with model: {evaluator.llm.ollama_model}")
    else:
        print("LLM router initialized (Ollama).")
except Exception as e:
    print(f"Error checking LLM: {e}")

print("\n--- Testing Ollama Regex Fallback ---")
dummy_ollama_output = """Based on the job posting, I would evaluate this job's match type as:
* Worth Trying (WT)
As for the recommended resume type (TPM), I would recommend:
* TPM (Transformational Product Manager)"""

match, rec, *_ = evaluator.parse_evaluation(dummy_ollama_output)
print(f"Parsed Match Type: {match}")
print(f"Parsed Resume:     {rec}")
