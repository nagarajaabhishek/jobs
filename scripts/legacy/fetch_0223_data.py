import os
import json
from datetime import datetime
from src.core.google_sheets_client import GoogleSheetsClient

def fetch_data(date_str):
    client = GoogleSheetsClient()
    client.connect()
    
    try:
        spreadsheet = client.client.open(client.sheet_name)
        worksheet = spreadsheet.worksheet(date_str)
        records = worksheet.get_all_records()
        
        output_file = f"data/raw_jobs_{date_str}.json"
        with open(output_file, "w") as f:
            json.dump(records, f, indent=2)
        
        print(f"Successfully fetched {len(records)} records from {date_str} to {output_file}")
        return records
    except Exception as e:
        print(f"Error fetching data for {date_str}: {e}")
        return None

if __name__ == "__main__":
    fetch_data("2026-02-23")
