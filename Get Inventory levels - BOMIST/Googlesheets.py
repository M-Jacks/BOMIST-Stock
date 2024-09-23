import pygsheets
from dotenv import load_dotenv
import os

load_dotenv()

path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
worksheet_title = os.getenv("WORKSHEET_TITLE")
sheetname = os.getenv("SHEET_NAME")

def fetch_parts_from_Sheets():
    try:
        gc = pygsheets.authorize(service_account_file=path)
        sh = gc.open(sheetname)
        sheet = sh.worksheet_by_title(worksheet_title)

        part_numbers = sheet.get_col(1, include_tailing_empty=False)[0:]  
        print(part_numbers)
        # Format the data 
        parts_data = []
        for part_number in zip(part_numbers):
            parts_data.append({
                "part": {
                    "mpn": part_number,
                }
            })
        return parts_data
    except Exception as e:
        print(f"Error fetching parts from Google Sheets: {e}")
        return []
