import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def cleanup_sheet():
    client = GoogleSheetsClient()
    client.connect()
    ws = client.sheet
    headers = [h.strip() for h in ws.row_values(1)]
    
    print(f"Current headers: {headers}")
    
    # 1. Prune redundant columns
    to_delete = ["Job Description", "Sourcing Tags", "Location Verification"]
    for col_name in to_delete:
        if col_name in headers:
            idx = headers.index(col_name) + 1
            print(f"Deleting '{col_name}' at column {idx}...")
            ws.delete_columns(idx)
            headers = [h.strip() for h in ws.row_values(1)] # Refresh

    # 2. Ensure Reasoning exists
    if "Reasoning" not in headers:
        # Insert after H1B
        if "H1B Sponsorship" in headers:
            insertion_idx = headers.index("H1B Sponsorship") + 2
            print(f"Inserting 'Reasoning' at column {insertion_idx}...")
            ws.insert_cols([["Reasoning"]], insertion_idx)
    
    print("Cleanup complete!")

if __name__ == "__main__":
    cleanup_sheet()
