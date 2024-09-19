# auth.py
import pygsheets
from dotenv import load_dotenv
import os

load_dotenv()

path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
sheet_name = os.getenv("SHEET_NAME")
worksheet_title = os.getenv("WORKSHEET_TITLE")

def authenticate_google_sheets():
    try:
        gc = pygsheets.authorize(service_account_file=path)
        sh = gc.open(sheet_name)
        sheet = sh.worksheet_by_title(worksheet_title)
        return sheet
    except Exception as e:
        print(f"Error authenticating with Google Sheets: {e}")
        exit()
