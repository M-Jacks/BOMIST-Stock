import requests
from dotenv import load_dotenv
import os

load_dotenv()

bomist_api_url = os.getenv("BOMIST_API_URL")

def fetch_parts_from_BOMIST():
    try:
        response = requests.get(bomist_api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        print("BOMIST connection refused (start local server)")
        exit()
