import os
from dotenv import load_dotenv
from nexarClient import NexarClient
from quote_utils import get_best_quote
from bomist import fetch_parts_from_BOMIST
from sheets import fetch_parts_from_Sheets  

load_dotenv()

batch_size = 5

client_id = os.getenv("NEXAR_CLIENT_ID")
client_secret = os.getenv("NEXAR_CLIENT_SECRET")

# GraphQL query to get pricing by stock levels
QUERY_PRICING_BY_VOLUME = '''
query pricingByVolumeLevels($mpn: String!) {
  supSearchMpn(q: $mpn, limit: 1) {
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

if __name__ == '__main__':
    try:
        """_summary_
        Make sure to comment out one source of parts data
        """
        # parts_data = fetch_parts_from_BOMIST()  # Fetch parts from BOMIST
        parts_data = fetch_parts_from_Sheets()  # Fetch parts from Google Sheets

        nexar_client = NexarClient(client_id, client_secret)

        for i in range(0, len(parts_data), batch_size):
            batch = parts_data[i:i + batch_size]

            for part_entry in batch:
                try:
                    part = part_entry.get("part")
                    part_number = part.get("mpn")
                    inventory = part.get("stock")

                    # Skip empty part numbers or stock
                    if not part_number or inventory is None:
                        continue  # Skip 
                      
                    print(f"\nProcessing Part Number: {part_number}, Current stock: {inventory}")
                    
                    if inventory == 0:
                        print("Skipping; - 0 stock available.")
                        continue  # Skip 
                      
                    # Run the GraphQL query for the current part number
                    variables = {"mpn": part_number}
                    results = nexar_client.get_query(QUERY_PRICING_BY_VOLUME, variables)
                    
                    if results:
                        parts = results.get('supSearchMpn', {}).get('results', [])
                        if parts:
                            mouser_or_lcsc_found = False
                            for item in parts:
                                part = item.get('part', {})
                                best_price = None
                                best_quantity = None

                                # Check sellers for quotes
                                if part.get('sellers'):
                                    for seller in part['sellers']:
                                        company_name = seller.get('company', {}).get('name', 'N/A')

                                        if company_name in ['Mouser', 'LCSC']:
                                            mouser_or_lcsc_found = True
                                            if seller.get('offers'):
                                                for offer in seller['offers']:
                                                    if offer.get('prices'):
                                                        print(f'  Full Quotes from {company_name}:')
                                                        for price_info in offer['prices']:
                                                            quantity = price_info.get('quantity', 'N/A')
                                                            price = price_info.get('price', 'N/A')
                                                            print(f'    Quantity: {quantity}, Price: ${price}')

                                                        prices = offer['prices']
                                                        price, quantity = get_best_quote(prices, inventory)

                                                        if price is not None:
                                                            best_price = price
                                                            best_quantity = quantity
                                                            print(f'Company: {company_name}')
                                                            print(f'  Best Quantity: {best_quantity}, Best Price: ${best_price}')
                                                print()

                            if not mouser_or_lcsc_found:
                                print("Skipping; - No Quote from Mouser and LCSC, try another company.")
                                continue

                            if best_price is None:
                                print("Skipping; - No best quote.")
                                continue
                        else:
                            print(f'No parts found for MPN: {part_number}.')
                    else:
                        print(f'No results returned for MPN: {part_number}.')
                except Exception as part_error:
                    print(f"Error processing part {part_entry}: {part_error}")
    except Exception as e:
        print(f'An error occurred: {e}')
