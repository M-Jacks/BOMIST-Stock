import os
import requests
import pygsheets
import time
from dotenv import load_dotenv

load_dotenv()

bomist_api_url = os.getenv("BOMIST_API_URL")
mouser_api_key = os.getenv("MOUSER_API_KEY")
mouser_api_url = os.getenv("MOUSER_API_URL")
future_api_key = os.getenv("FUTURE_API_KEY")
future_api_url = os.getenv("FUTURE_API_URL")
path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
sheet_name = os.getenv("SHEET_NAME")
worksheet_title = os.getenv("WORKSHEET_TITLE")
batch_size = 5

try:
    gc = pygsheets.authorize(service_account_file=path)
except Exception as e:
    print(f"Error authenticating with Google Sheets: {e}")
    exit()

sh = gc.open(sheet_name)
sheet = sh.worksheet_by_title(worksheet_title)

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
            return None, None, "Mouser"

        if data["SearchResults"]["NumberOfResult"] > 0:
            part_info = data["SearchResults"]["Parts"][0]
            price_breaks = part_info.get("PriceBreaks", [])

            if not price_breaks:
                return None, None, "Mouser"

            # Sort price breaks by quantity in ascending order
            price_breaks = sorted(price_breaks, key=lambda x: x["Quantity"])

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

            return best_price, best_quantity, "Mouser"

        return None, None, "Mouser"  # Return Mouser as source if no suitable price breaks found

    except requests.RequestException as e:
        print(f"Failed to fetch Mouser data for part {part_number}: {e}")
        return None, None, "Mouser"

# Get the best quote from Future Electronics
def get_future_quote(part_number, inventory):
    headers = {
        "Accept": "application/json,text/javascript",
        "Content-Type": "application/json",
        "x-orbweaver-licensekey": future_api_key
    }

    params = {
        'part_number': part_number,
        'lookup_type': 'contains'
    }

    try:
        response = requests.get(future_api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if 'offers' in data and data['offers']:
            offer = data['offers'][0]
            quantities = offer.get('quantities', {})
            pricing = offer.get('pricing', [])
            
            quantity_available = quantities.get('quantity_available', 0)
            quantity_on_order = quantities.get('quantity_on_order', 0)
            total_quantity = quantity_available + quantity_on_order

            if pricing:
                unit_price = pricing[0]['unit_price']
                total_value = total_quantity * unit_price
                return unit_price, total_quantity, "Future"
            else:
                print(f"No pricing information available for part {part_number} on Future Electronics.")
                return None, None, "Future"
        else:
            print(f"No offers found for part {part_number} on Future Electronics.")
            return None, None, "Future"

    except requests.RequestException as e:
        print(f"Failed to fetch Future Electronics data for part {part_number}: {e}")
        return None, None, "Future"

def calculate_inventory_value(part_number, inventory):
    best_price, best_quantity, source = get_best_quote(part_number, inventory)
    
    if best_price is None or best_quantity is None:
        print(f"Part {part_number} not found on Mouser. Searching Future Electronics...")
        # Try Future Electronics if Mouser fails
        best_price, best_quantity, source = get_future_quote(part_number, inventory)
        if best_price is None or best_quantity is None:
            print(f"Part {part_number} not found on Future Electronics. Skipping.")
            return None, None, None
    else:
        total_value = (inventory * best_price) / best_quantity

    return best_price, best_quantity, source

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
sheet.update_value('F1', 'Source')

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
            best_price, best_quantity, source = result
            total_value = (inventory * best_price) / best_quantity if best_quantity else 0
            print(f"Part: {part_number}, Inventory: {inventory}, Best Price: ${best_price}, Quantity: {best_quantity}, Total Value: ${total_value}, Source: {source}")

            sheet.update_value(f'A{starting_row_index}', part_number)
            sheet.update_value(f'B{starting_row_index}', inventory)
            sheet.update_value(f'C{starting_row_index}', f"${best_price}")
            sheet.update_value(f'D{starting_row_index}', best_quantity)
            sheet.update_value(f'E{starting_row_index}', f"${total_value}")
            sheet.update_value(f'F{starting_row_index}', source)

            starting_row_index += 1  # next row for the next part

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
