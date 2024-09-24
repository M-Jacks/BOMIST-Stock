import pygsheets
import os
from dotenv import load_dotenv

load_dotenv()

path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
sheet_name = os.getenv("SHEET_NAME")
worksheet_title = os.getenv("WORKSHEET_TITLE")

def authenticate_google_sheets():
    """Authenticate and return the Google Sheets worksheet."""
    try:
        gc = pygsheets.authorize(service_account_file=path)
        sh = gc.open(sheet_name)
        return sh.worksheet_by_title(worksheet_title)
    except Exception as e:
        print(f"Error authenticating with Google Sheets: {e}")
        return None

def update_google_sheet(sheet, data):
    """Update Google Sheets with the given data."""
    starting_row_index = 2 

    sheet.update_value('A1', 'Part Number')
    sheet.update_value('B1', 'Current Stock')
    sheet.update_value('C1', 'Low Stock Threshold')

    for part_data in data:
        part_number, inventory, low_stock_threshold = part_data
        sheet.update_value(f'A{starting_row_index}', part_number)
        sheet.update_value(f'B{starting_row_index}', inventory)
        sheet.update_value(f'C{starting_row_index}', low_stock_threshold or "N/A")
        starting_row_index += 1

def log_summary(sheet, total_parts, execution_time):
    """Log the summary of processed parts and execution time."""
    summary_row_index = total_parts + 4
    sheet.update_value(f'A{summary_row_index}', 'Total Parts Processed:')
    sheet.update_value(f'B{summary_row_index}', total_parts)
    sheet.update_value(f'A{summary_row_index + 1}', 'Total Execution Time:')
    sheet.update_value(f'B{summary_row_index + 1}', f"{execution_time:.2f} seconds")
