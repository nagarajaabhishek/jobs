import json
import pandas as pd
from collections import Counter

def analyze_0223_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    print("--- 02/23 Data Analysis ---")
    print(f"Total Jobs: {len(df)}")
    
    if 'Match Type' in df.columns:
        print("\nMatch Type Distribution:")
        dist = df['Match Type'].value_counts()
        for idx, val in dist.items():
            print(f"  {idx}: {val}")
    
    if 'Reasoning' in df.columns:
        no_jd_count = df['Reasoning'].str.contains('JD content is not provided|No JD in cache', case=False, na=False).sum()
        print(f"\nJobs with missing JD mentions in reasoning: {no_jd_count} ({100*no_jd_count/len(df):.1f}%)")

if __name__ == "__main__":
    analyze_0223_data("data/raw_jobs_2026-02-23.json")
