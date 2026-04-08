import os
import sys

import gspread

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient


def reset_empty_reasoning():
    client = GoogleSheetsClient()
    client.connect()

    print("\n--- Resetting bad / empty reasoning rows (Status -> NEW) ---")
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
        reason_clean = (reason or "").strip()
        reason_l = reason_clean.lower()

        is_empty = (
            not reason_clean
            or reason_clean in ("N/A", "LLM failed", "Parse failed", "[N/A] Parse failed")
            or "parse failed" in reason_l
            or "llm failed" in reason_l
        )
        is_too_short = len(reason_clean) < 30

        if status == "EVALUATED" and (is_empty or is_too_short):
            cells_to_update.append(gspread.Cell(row=row_idx, col=status_idx + 1, value="NEW"))
            reset_count += 1

    if cells_to_update:
        print(f"Resetting {reset_count} rows back to 'NEW' for re-evaluation...")
        ws.update_cells(cells_to_update)
        print("Done. Re-run evaluation (e.g. python3 apps/cli/run_pipeline.py) with updated code.")
    else:
        print("No matching rows found to reset.")


if __name__ == "__main__":
    reset_empty_reasoning()
