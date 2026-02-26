import sys
import os
import re

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.job_filters import passes_sourcing_filter

def test_filters():
    test_jobs = [
        {"title": "Business Systems Analyst", "location": "Dallas, TX", "description": "Looking for BA."},
        {"title": "Technical Project Manager", "location": "Remote", "description": "Need a PM."},
        {"title": "Senior Product Manager", "location": "Austin", "description": "Sr role."},
        {"title": "Healthcare BA", "location": "Dubai", "description": "BA role."},
        {"title": "IT Project Manager (PMO)", "location": "USA", "description": "PMO role."},
    ]
    
    print("\n--- Testing Sourcing Filters ---\n")
    for job in test_jobs:
        passed, reason = passes_sourcing_filter(job)
        status = "✅ PASS" if passed else f"❌ FAIL ({reason})"
        print(f"Title: {job['title']:<30} | Status: {status}")

if __name__ == "__main__":
    test_filters()
