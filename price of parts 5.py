import os
import requests
import pygsheets
import time
from dotenv import load_dotenv

# Get environment variables
load_dotenv()

# Config
bomist_api_url = os.getenv('BOMIST_API_URL')
mouser_api_key = os.getenv('MOUSER_API_KEY')
mouser_api_url = "https://api.mouser.com/api/v1/search/keyword"
batch_size = 5  # Number of parts to process per batch

path = r'D:\dev\Misikhu\CSB2_AMT_DEV_ZONE\Pygsheets\secret-outpost-407111-8f88417a2d28.json'

# Authenticate with Google Sheets
gc = pygsheets.authorize(service_account_file=path)
sheetname = "sheetsdemo"
sh = gc.open(sheetname)
sheet = sh.worksheet_by_title('Sheet7')

def get_best_quote(part_number, inventory):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "SearchByKeywordRequest": {
            "keyword": part_number
        }
    }
    params = {
        "apiKey": mouser_api_key
    }

    try:
        response = requests.post(mouser_api_url, json=payload, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["Errors"]:
            print(f"Error fetching Mouser data for part {part_number}: {data['Errors']}")
            return None, None

        if data["SearchResults"]["NumberOfResult"] > 0:
            part_info = data["SearchResults"]["Parts"][0]
            price_breaks = part_info.get("PriceBreaks", [])
            if not price_breaks:
                return None, None

            # Sort price breaks by quantity in ascending order
            print(price_breaks)
            price_breaks = sorted(price_breaks, key=lambda x: x["Quantity"])

            best_price = None
            best_quantity = None
            for price_break in price_breaks:
                quantity = price_break["Quantity"]
                price = float(price_break["Price"].strip('$'))

                if quantity <= inventory:
                    best_price = price
                    best_quantity = quantity
                else:
                    break

            return best_price, best_quantity

        return None, None  # Return None if no suitable price breaks found

    except requests.RequestException as e:
        print(f"Failed to fetch Mouser data for part {part_number}: {e}")
        return None, None

# calculate the total value of the inventory
def calculate_inventory_value(part_number, inventory):
    best_price, best_quantity = get_best_quote(part_number, inventory)
    if best_price is None or best_quantity is None:
        print(f"Missing or invalid data for part {part_number}. Skipping.")
        return None

    if best_quantity == 0:
        print(f"Best quantity is zero for part {part_number}. Skipping.")
        return None

    total_value = (inventory * best_price) / best_quantity
    return best_price, best_quantity, total_value

# Fetch parts from BOMIST
try:
    response = requests.get(bomist_api_url)
    response.raise_for_status()
    parts_data = response.json()
except requests.RequestException:
    print("BOMIST connection refused (start local server)")
    exit()

total_parts = 0
start_time = time.time()

# starting row and column indexes
starting_row_index = 2  
start_col_index = 'a'

# Set column headers
sheet.update_value('I1', 'Part Number')
sheet.update_value('J1', 'Current Stock')
sheet.update_value('K1', 'Best Price')
sheet.update_value('L1', 'Best Quantity')
sheet.update_value('M1', 'Total Value')

# Process parts in batches
for i in range(0, len(parts_data), batch_size):
    batch = parts_data[i:i + batch_size]

    # Calculate inventory value for each part in the batch
    for part_entry in batch:
        part = part_entry.get("part")
        part_number = part.get("mpn")
        inventory = part.get("stock")

        print(f"Part Number: {part_number}")
        print(f"Current stock: {inventory}")

        if not part_number:
            print("Missing part number. Skipping.")
            continue
        if inventory is None:
            print(f"Missing inventory for part {part_number}. Skipping.")
            continue

        result = calculate_inventory_value(part_number, inventory)
        if result:
            best_price, best_quantity, total_value = result
            print(f"Part: {part_number}, Inventory: {inventory}, Best Price: ${best_price}, Quantity: {best_quantity}, Total Value: ${total_value}")

            # Update Google Sheet 
            sheet.update_value(f'I{starting_row_index}', part_number)
            sheet.update_value(f'J{starting_row_index}', inventory)
            sheet.update_value(f'K{starting_row_index}', f"${best_price}")
            sheet.update_value(f'L{starting_row_index}', best_quantity)
            sheet.update_value(f'M{starting_row_index}', f"${total_value}")

            starting_row_index += 1  # Move to the next row for the next part

        else:
            print(f"Failed to calculate value for part {part_number}")

        total_parts += 1

end_time = time.time()
execution_time = end_time - start_time

print(f"Total Parts Processed: {total_parts}")
print(f"Total Execution Time: {execution_time} seconds")
