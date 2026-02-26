import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def inspect_rows():
    client = GoogleSheetsClient()
    sheet = client.client.open(client.sheet_name)
    worksheet = sheet.worksheet("2026-02-23")
    rows = worksheet.get_all_records()
    
    print(f"\n--- Raw Row Inspection (First 5) ---")
    for i, row in enumerate(rows[:5]):
        print(f"Row {i+1}: {row.get('Role Title')} | Match Type: [{row.get('Match Type')}] | Score: [{row.get('Score')}]")

if __name__ == "__main__":
    inspect_rows()
