from src.core.google_sheets_client import GoogleSheetsClient
client = GoogleSheetsClient()
client.connect()
records = client.sheet.get_all_records()
print(f"Total jobs: {len(records)}")
if records:
    print(f"First job status: {records[0].get('Status')}")
    print(f"First job desc length: {len(str(records[0].get('Job Description', '')))}")
    
new_jobs = [r for r in records if r.get('Status') == 'NEW']
print(f"Found {len(new_jobs)} 'NEW' jobs.")
