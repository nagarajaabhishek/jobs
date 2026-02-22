from src.agents.evaluate_jobs import JobEvaluator

def main():
    print("--- Starting Re-Evaluation of 'Maybe' Jobs ---")
    evaluator = JobEvaluator()
    # Pull 'Maybe' jobs and re-evaluate them with the new calibrated prompt
    evaluator.evaluate_all(mode="MAYBE", limit=200)
    print("--- Re-Evaluation Complete ---")

if __name__ == "__main__":
    main()
