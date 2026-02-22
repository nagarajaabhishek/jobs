from src.core.google_sheets_client import GoogleSheetsClient
from datetime import datetime

client = GoogleSheetsClient()
client.connect()
today_str = datetime.now().strftime("%Y-%m-%d")
worksheet = client.client.open(client.sheet_name).worksheet(today_str)
headers = worksheet.row_values(1)
print(headers)
