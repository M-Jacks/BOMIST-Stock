import os
from dotenv import load_dotenv
from nexarClient import NexarClient  

load_dotenv()

client_id = os.getenv("NEXAR_CLIENT_ID")
client_secret = os.getenv("NEXAR_CLIENT_SECRET")

# GraphQL query to get pricing by volume levels
QUERY_PRICING_BY_VOLUME = '''
query pricingByVolumeLevels {
  supSearchMpn(
    q: "0603B103K500NT",
    limit: 1) {
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
        nexar_client = NexarClient(client_id, client_secret)
        
        # Run the GraphQL query
        variables = {}  # no variables are needed for this query
        results = nexar_client.get_query(QUERY_PRICING_BY_VOLUME, variables)
        
        if results:
            parts = results.get('supSearchMpn', {}).get('results', [])
            if parts:
                for item in parts:
                    part = item.get('part', {})
                    mouser_or_lcsc_found = False  # Initialize flag to track presence of Mouser or LCSC
                    
                    if part.get('sellers'):
                        for seller in part['sellers']:
                            company_name = seller.get('company', {}).get('name', 'N/A')
                            
                        # Filter for Mouser and LCSC only
                        # if company_name in ['Mouser', 'LCSC']:
                            mouser_or_lcsc_found = True  # Mark that at least one of them is found
                            print(f'Company: {company_name}')
                            
                            if seller.get('offers'):
                                for offer in seller['offers']:
                                    if offer.get('prices'):
                                        for price_info in offer['prices']:
                                            quantity = price_info.get('quantity', 'N/A')
                                            price = price_info.get('price', 'N/A')
                                            print(f'  Quantity: {quantity}, Price: {price}')
                                print()
                    
                    # If neither Mouser nor LCSC is found...
                    if not mouser_or_lcsc_found:
                        print("Part not available on Mouser or LCSC.")
            else:
                print('No parts found for this query.')
        else:
            print('No results returned from the query.')
    except Exception as e:
        print(f'An error occurred: {e}')
