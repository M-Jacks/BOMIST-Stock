# utils.py
from mouser import get_best_quote

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
