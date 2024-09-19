# main.py
from bestQuote import get_best_quote

if __name__ == '__main__':
    part_number = "0805W8F3600T5E"
    available_stock = 230
    
    best_quantity, best_price = get_best_quote(part_number, available_stock)
    
    if best_quantity and best_price:
        print(f"Best Quantity: {best_quantity}, Best Price: {best_price}")
    else:
        print("No suitable quote found for this part.")
