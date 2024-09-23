import time
from Bomist import fetch_parts_data
from sheets import authenticate_google_sheets, update_google_sheet, log_summary

low_stock_threshold = 10  # Default value if low stock is missing
batch_size = 5  # Number of parts to process at a time

def process_parts(parts_data, low_stock_threshold):
    """Process parts and return those with low stock or no stock."""
    processed_parts = []
    for part_entry in parts_data:
        part = part_entry.get("part")
        part_number = part.get("mpn")
        inventory = part.get("stock")
        part_low_stock = part.get("lowStock", low_stock_threshold)

        if not part_number or inventory is None:
            continue  # Skip if part number or inventory is missing

        # Check if stock is 0 or below the low stock threshold
        if inventory == 0 or (part_low_stock and inventory < part_low_stock):
            print(f"Part {part_number} has low stock: {inventory}")
            processed_parts.append((part_number, inventory, part_low_stock))

    return processed_parts

def main():
    start_time = time.time()

    parts_data = fetch_parts_data()
    if parts_data is None:
        return  # Exit if BOMIST connection failed

    sheet = authenticate_google_sheets()
    if sheet is None:
        return  # Exit if Google Sheets authentication failed

    processed_parts = process_parts(parts_data, low_stock_threshold)

    update_google_sheet(sheet, processed_parts)

    # summary
    execution_time = time.time() - start_time
    log_summary(sheet, len(processed_parts), execution_time)

    print(f"Total Parts Processed: {len(processed_parts)}")
    print(f"Total Execution Time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()
