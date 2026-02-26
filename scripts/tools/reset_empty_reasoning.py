import sys
import os
import gspread
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def reset_empty_reasoning():
    client = GoogleSheetsClient()
    client.connect()
    
    print("\n--- Resetting Empty Reasoning Rows ---")
    ws = client.sheet
    values = ws.get_all_values()
    if not values:
        print("Empty sheet.")
        return
        
    headers = [h.strip() for h in values[0]]
    status_idx = headers.index("Status") if "Status" in headers else -1
    reason_idx = headers.index("Reasoning") if "Reasoning" in headers else -1
    
    if status_idx == -1 or reason_idx == -1:
        print("Missing required columns.")
        return
        
    cells_to_update = []
    reset_count = 0
    
    for i, row in enumerate(values[1:]):
        row_idx = i + 2
        status = row[status_idx] if len(row) > status_idx else ""
        reason = row[reason_idx] if len(row) > reason_idx else ""
        
        # If it's evaluated but has N/A or empty reasoning, or reasoning is too short (just location)
        is_empty = not reason or reason.strip() in ["N/A", "LLM failed", "Parse failed"]
        is_too_short = len(reason.strip()) < 30 # Usually location prefix + tiny snippet
        
        if status == "EVALUATED" and (is_empty or is_too_short):
            # Change status back to NEW
            cells_to_update.append(gspread.Cell(row=row_idx, col=status_idx + 1, value="NEW"))
            reset_count += 1
            
    if cells_to_update:
        print(f"Resetting {reset_count} roles back to 'NEW' for re-evaluation...")
        ws.update_cells(cells_to_update)
        print("Done.")
    else:
        print("No empty reasoning rows found to reset.")

if __name__ == "__main__":
    reset_empty_reasoning()
