import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def debug_reasoning():
    client = GoogleSheetsClient()
    client.connect()
    ws = client.sheet
    headers = [h.strip() for h in ws.row_values(1)]
    
    print("\n--- Sheet Diagnostics ---")
    print(f"Tab: {ws.title}")
    print(f"Headers: {headers}")
    
    reason_col = client._get_or_create_col_index(ws, "Reasoning", headers)
    match_col = client._get_or_create_col_index(ws, "Match Type", headers)
    
    print(f"Reasoning Column Index: {reason_col}")
    print(f"Match Type Column Index: {match_col}")
    
    # Check first few rows
    values = ws.get_all_values()
    if len(values) > 1:
        print("\nChecking first 5 evaluated rows:")
        count = 0
        for i, row in enumerate(values[1:]):
            status = row[0]
            if status == "EVALUATED":
                match_val = row[match_col-1] if len(row) >= match_col else "N/A"
                reason_val = row[reason_col-1] if len(row) >= reason_col else "N/A"
                print(f"Row {i+2}: Match={match_val} | Reason Snippet={reason_val[:50]}...")
                count += 1
                if count >= 5: break
    else:
        print("No data rows found.")

if __name__ == "__main__":
    debug_reasoning()
