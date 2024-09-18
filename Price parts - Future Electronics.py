import requests
from dotenv import load_dotenv
import os

load_dotenv()

def search_part_number(part_number):
    api_key = os.getenv('FUTURE_API_KEY')
    
    if not api_key:
        raise ValueError("API key not found. Make sure it's in the .env file.")
    
    url = f"https://api.futureelectronics.com/api/v1/pim-future/lookup?part_number={part_number}&lookup_type=contains"
    
    headers = {
        'Accept': 'application/json,text/javascript',
        'host': 'api.futureelectronics.com',
        'Content-Type': 'application/json',
        'x-orbweaver-licensekey': api_key
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if 'offers' in data and data['offers']:
            offer = data['offers'][0]
            quantities = offer.get('quantities', {})
            pricing = offer.get('pricing', [])
            
            quantity_available = quantities.get('quantity_available', 0)
            quantity_on_order = quantities.get('quantity_on_order', 0)
            total_quantity = quantity_available + quantity_on_order

            if pricing:
                unit_price = pricing[0]['unit_price']
                total_value = total_quantity * unit_price
                print(f"Part Number: {part_number}")
                print(f"Total Quantity Available: {total_quantity}")
                print(f"Unit Price: ${unit_price}")
                print(f"Total Value: ${total_value:.2f}")
            else:
                print(f"No pricing information available for part {part_number}")
        else:
            print(f"No offers found for part {part_number}")
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.text}")

part_number = '0603WAF1000T5E'
search_part_number(part_number)
