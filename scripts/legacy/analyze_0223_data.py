import json
import pandas as pd
from collections import Counter

def analyze_0223_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    print("--- 02/23 Data Analysis ---")
    print(f"Total Jobs: {len(df)}")
    
    if 'Status' in df.columns:
        print("\nStatus Distribution:")
        print(df['Status'].value_counts())
    
    if 'Match Type' in df.columns:
        print("\nMatch Type Distribution:")
        print(df['Match Type'].value_counts())
    
    if 'H1B Sponsorship' in df.columns:
        print("\nH1B Sponsorship Breakdown:")
        print(df['H1B Sponsorship'].value_counts())
        
    print("\nTop 5 Reasoning Snippets (Rejections):")
    rejections = df[df['Match Type'].str.lower().str.contains('no|not at all', na=False)]
    for reason in rejections['Reasoning'].head(5):
        print(f"- {reason}")
        
    print("\nTop 5 Reasoning Snippets (Strong Matches):")
    strong_matches = df[df['Match Type'].str.lower().str.contains('strong|sure', na=False)]
    for reason in strong_matches['Reasoning'].head(5):
        print(f"- {reason}")

if __name__ == "__main__":
    analyze_0223_data("data/raw_jobs_2026-02-23.json")
