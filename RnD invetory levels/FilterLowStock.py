import pygsheets
import os
from dotenv import load_dotenv

load_dotenv()

def authenticate_and_open_sheet(path, sheetname, worksheet_title):
    """Authenticate using the given path and return the specified worksheet."""
    gc = pygsheets.authorize(service_account_file=path)
    sh = gc.open(sheetname)
    return sh.worksheet_by_title(worksheet_title)

def get_column_data(sheet, column_number):
    """Retrieve data from a specific column, excluding the header."""
    return sheet.get_col(column_number, include_tailing_empty=False)[1:]

def filter_low_stock_parts(part_numbers, labels, stock_balances, threshold=10):
    """Filter parts with stock balance less than or equal to the threshold."""
    low_stock_parts = []
    for part_number, label, stock_balance in zip(part_numbers, labels, stock_balances):
        try:
            stock_balance_int = int(stock_balance)
            if stock_balance_int <= threshold:
                low_stock_parts.append([part_number, label, stock_balance])
        except ValueError:
            print(f"Skipping invalid stock balance value for Part Number: {part_number}")
    return low_stock_parts

def ensure_sheet_exists(sh, sheet_name):
    """Check if the sheet exists, create if not, and return the sheet."""
    try:
        sheet = sh.worksheet_by_title(sheet_name)
    except pygsheets.WorksheetNotFound:
        sheet = sh.add_worksheet(sheet_name)
    return sheet

def update_sheet_with_data(sheet, data, start_cell='A1'):
    """Clear existing data in the sheet and update it with new data."""
    sheet.clear()
    sheet.update_values(start_cell, data)

def main():
    path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    sheetname = os.getenv("SHEET_NAME")
    worksheet_title = os.getenv("WORKSHEET_TITLE")
    target_sheet_name = os.getenv("target_sheet_name")
    
    main_sheet = authenticate_and_open_sheet(path, sheetname, worksheet_title)
    
    part_numbers = get_column_data(main_sheet, 5)  # Column E
    labels = get_column_data(main_sheet, 4)        # Column D
    stock_balances = get_column_data(main_sheet, 9)  # Column I

    low_stock_parts = filter_low_stock_parts(part_numbers, labels, stock_balances)
    
    sh = main_sheet.spreadsheet
    outputSheet = ensure_sheet_exists(sh, target_sheet_name)
    
    # Prepare data and update the sheet
    if low_stock_parts:
        header = [['Part Number', 'Label', 'Stock Balance']]
        data_to_write = header + low_stock_parts
        update_sheet_with_data(outputSheet, data_to_write)
    else:
        print("No parts found with stock balance <= 10")

# Run the main function
if __name__ == "__main__":
    main()
