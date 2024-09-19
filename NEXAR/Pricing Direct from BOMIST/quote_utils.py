def get_best_quote(prices, available_stock):
    """Find the best price for the given stock from price breaks."""
    # Filter out prices where quantity is greater than available stock
    filtered_prices = [p for p in prices if p['quantity'] <= available_stock]
    
    if filtered_prices:
        """Find the best price among the filtered prices"""
        best_price_info = min(filtered_prices, key=lambda p: float(p['price']) if isinstance(p['price'], float) else float(p['price'].strip('$')))
        best_quantity = best_price_info['quantity']
        best_price = float(best_price_info['price']) if isinstance(best_price_info['price'], float) else float(best_price_info['price'].strip('$'))
        return best_price, best_quantity
    else:
        """If no prices fit the available stock, pick the smallest quantity and its price"""
        smallest_quantity_info = min(prices, key=lambda p: p['quantity'])
        best_quantity = smallest_quantity_info['quantity']
        best_price = float(smallest_quantity_info['price']) if isinstance(smallest_quantity_info['price'], float) else float(smallest_quantity_info['price'].strip('$'))
        return best_price, best_quantity
