import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.job_filters import passes_sourcing_filter

def test_filter():
    # Example JobSpy result that failed earlier
    job = {
        "title": "Product Manager",
        "location": "Lehi, UT, US",
        "description": "Looking for a PM...",
        "company": "Some Tech Co",
        "url": "https://indeed.com/viewjob?jk=123"
    }
    
    passed, reason = passes_sourcing_filter(job)
    print(f"\n--- Filter Test ---")
    print(f"Job: {job['title']} in {job['location']}")
    print(f"Passed: {passed}")
    if not passed:
        print(f"Reason: {reason}")

if __name__ == "__main__":
    test_filter()
