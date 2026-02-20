from llm_router import LLMRouter
from evaluate_jobs import JobEvaluator

import logging
logging.basicConfig(level=logging.ERROR)

evaluator = JobEvaluator()

print("--- Testing OpenAI Configuration ---")
try:
    if evaluator.llm.openai_client:
        print("OpenAI client successfully initialized via API key.")
    else:
        print("OpenAI client FAILED to initialize.")
except Exception as e:
    print(f"Error checking OpenAI: {e}")

print("\n--- Testing Ollama Regex Fallback ---")
dummy_ollama_output = """Based on the job posting, I would evaluate this job's match type as:
* Worth Trying (WT)
As for the recommended resume type (TPM), I would recommend:
* TPM (Transformational Product Manager)"""

match, rec, _ = evaluator.parse_evaluation(dummy_ollama_output)
print(f"Parsed Match Type: {match}")
print(f"Parsed Resume:     {rec}")

