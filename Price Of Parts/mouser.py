# mouser.py
import requests
from dotenv import load_dotenv
import os

load_dotenv()

mouser_api_key = os.getenv("MOUSER_API_KEY")
mouser_api_url = os.getenv("MOUSER_API_URL")

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
