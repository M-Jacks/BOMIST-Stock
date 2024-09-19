# bestQuote.py
from nexarClient import NexarClient  
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv("NEXAR_CLIENT_ID")
client_secret = os.getenv("NEXAR_CLIENT_SECRET")

# GraphQL query template to get pricing by volume levels
QUERY_PRICING_BY_VOLUME = '''
query pricingByVolumeLevels($partNumber: String!) {
  supSearchMpn(q: $partNumber, limit: 1) {
    hits
    results {
      part {
        sellers {
          company {
            name
          }
          offers {
            prices {
              quantity
              price
            }
          }
        }      
      }
    }
  }
}
'''

def fetch_part_price_breaks(part_number: str):
    """Fetches the part price breaks using Nexar API."""
    nexar = NexarClient(client_id, client_secret)
    
    # Run the query using the provided part number
    variables = {"partNumber": part_number}
    response = nexar.get_query(QUERY_PRICING_BY_VOLUME, variables)
    
    parts = response.get('supSearchMpn', {}).get('results', [])
    if not parts:
        return None, None

    # Collect price breaks from Mouser and LCSC
    price_breaks = []
    for part in parts:
        sellers = part.get('part', {}).get('sellers', [])
        for seller in sellers:
            company_name = seller.get('company', {}).get('name', 'N/A')
            if company_name in ['Mouser', 'LCSC']:
                offers = seller.get('offers', [])
                for offer in offers:
                    prices = offer.get('prices', [])
                    for price_info in prices:
                        quantity = price_info.get('quantity')
                        price = float(price_info.get('price'))
                        price_breaks.append((quantity, price))
    
    return price_breaks


def get_best_quote(part_number: str, available_stock: int):
    """Returns the best price and quantity for the given part based on available stock."""
    price_breaks = fetch_part_price_breaks(part_number)

    if not price_breaks:
        return None, None

    best_quantity = None
    best_price = None

    # Find the best price and quantity based on the available stock
    for quantity, price in price_breaks:
        if quantity <= available_stock and (best_quantity is None or quantity > best_quantity):
            best_quantity = quantity
            best_price = price

    return best_quantity, best_price
