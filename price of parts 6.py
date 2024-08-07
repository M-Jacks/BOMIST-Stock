import os
import requests
import pygsheets
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config
bomist_api_url = os.getenv("BOMIST_API_URL")
mouser_api_key = os.getenv("MOUSER_API_KEY")
mouser_api_url = os.getenv("MOUSER_API_URL")
batch_size = 5

path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

# Authentication
gc = pygsheets.authorize(service_account_file=path)
sheetname = "sheetsdemo"
sh = gc.open(sheetname)
sheet = sh.worksheet_by_title('Sheet9')

# Get the best quote from Mouser
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
            price_breaks = sorted(price_breaks, key=lambda x: x["Quantity"])

            # Take the price break with the least quantity if current stock is lower than the lowest price break quantity available
            best_price = float(price_breaks[0]["Price"].strip('$'))
            best_quantity = price_breaks[0]["Quantity"]

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

# Calculate the total value of the inventory
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


starting_row_index = 2  

# Column headers
sheet.update_value('A1', 'Part Number')
sheet.update_value('B1', 'Current Stock')
sheet.update_value('C1', 'Best Price')
sheet.update_value('D1', 'Best Quantity')
sheet.update_value('E1', 'Total Value')

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
            sheet.update_value(f'A{starting_row_index}', part_number if part_number else 'N/A')
            sheet.update_value(f'B{starting_row_index}', inventory if inventory else 'N/A')
            sheet.update_value(f'C{starting_row_index}', 'Skipped due to missing part number')
            starting_row_index += 1
            continue
        if inventory is None:
            print(f"Missing inventory for part {part_number}. Skipping.")
            sheet.update_value(f'A{starting_row_index}', part_number)
            sheet.update_value(f'B{starting_row_index}', inventory if inventory else 'N/A')
            sheet.update_value(f'C{starting_row_index}', 'Skipped due to missing inventory')
            starting_row_index += 1
            continue
        if inventory == 0:
            print(f"No stock for part {part_number}. Skipping.")
            sheet.update_value(f'A{starting_row_index}', part_number)
            sheet.update_value(f'B{starting_row_index}', inventory)
            sheet.update_value(f'C{starting_row_index}', "Skipped due to no stock")
            starting_row_index += 1
            continue

        result = calculate_inventory_value(part_number, inventory)
        if result:
            best_price, best_quantity, total_value = result
            print(f"Part: {part_number}, Inventory: {inventory}, Best Price: ${best_price}, Quantity: {best_quantity}, Total Value: ${total_value}")

            sheet.update_value(f'A{starting_row_index}', part_number)
            sheet.update_value(f'B{starting_row_index}', inventory)
            sheet.update_value(f'C{starting_row_index}', f"${best_price}")
            sheet.update_value(f'D{starting_row_index}', best_quantity)
            sheet.update_value(f'E{starting_row_index}', f"${total_value}")

            starting_row_index += 1  # next row for the next part

        else:
            mouser_response = get_best_quote(part_number, inventory)
            if mouser_response == (None, None):
                print(f"Part not on Mouser for part {part_number}")
                sheet.update_value(f'A{starting_row_index}', part_number)
                sheet.update_value(f'B{starting_row_index}', inventory)
                sheet.update_value(f'C{starting_row_index}', 'Skipped due to part not on Mouser')
            else:
                print(f"Failed to calculate value for part {part_number}")
                sheet.update_value(f'A{starting_row_index}', part_number)
                sheet.update_value(f'B{starting_row_index}', inventory)
                sheet.update_value(f'C{starting_row_index}', 'Skipped due to failed calculation')
            starting_row_index += 1

        total_parts += 1

end_time = time.time()
execution_time = end_time - start_time

summary_row_index = starting_row_index + 2
sheet.update_value(f'A{summary_row_index}', 'Total Parts Processed:')
sheet.update_value(f'B{summary_row_index}', total_parts)
sheet.update_value(f'A{summary_row_index + 1}', 'Total Execution Time:')
sheet.update_value(f'B{summary_row_index + 1}', f"{execution_time:.2f} seconds")

print(f"Total Parts Processed: {total_parts}")
print(f"Total Execution Time: {execution_time} seconds")
