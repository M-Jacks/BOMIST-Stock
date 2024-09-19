# main.py
import time
from auth import authenticate_google_sheets
from bomist import fetch_parts
from utils import calculate_inventory_value

batch_size = 5 

def main():
    sheet = authenticate_google_sheets()
    parts_data = fetch_parts()
    
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

if __name__ == '__main__':
    main()
