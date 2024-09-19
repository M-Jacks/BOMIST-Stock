import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Nexar API URL and the OAuth URL for getting the token
NEXAR_API_URL = os.getenv("NEXAR_API_URL")
OAUTH_URL = os.getenv("OAUTH_URL")

client_id = os.getenv("NEXAR_CLIENT_ID")
client_secret = os.getenv("NEXAR_CLIENT_SECRET")

# GraphQL query to get pricing by volume levels
QUERY_PRICING_BY_VOLUME = '''
query pricingByVolumeLevels {
  supSearchMpn(
    q: "APM32F103RBT6",
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

# Authenticate and get the OAuth token
def get_access_token():
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'supply.domain'
    }

    response = requests.post(OAUTH_URL, data=payload)
    response.raise_for_status()
    return response.json().get('access_token')

# Run the GraphQL query
def run_query(query):
    token = get_access_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(NEXAR_API_URL, json={'query': query}, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    try:
        results = run_query(QUERY_PRICING_BY_VOLUME)
        
        if results:
            parts = results.get('data', {}).get('supSearchMpn', {}).get('results', [])
            if parts:
                for item in parts:
                    part = item.get('part', {})
                    mouser_or_lcsc_found = False  # Initialize flag to track presence of Mouser or LCSC
                    
                    if part.get('sellers'):
                        for seller in part['sellers']:
                            company_name = seller.get('company', {}).get('name', 'N/A')
                            
                            # Filter for Mouser and LCSC only
                            if company_name in ['Mouser', 'LCSC']:
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
    except requests.RequestException as e:
        print(f'An error occurred: {e}')
