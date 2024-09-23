import requests
from Googlesheets import fetch_parts_from_Sheets as getMPNs
url = "http://localhost:3333/search"
batch_size= 5
payload = {"selector": {"part.mpn": "AMT49406GLPTR"}}
headers = {
    "Content-Type": "application/json",
}
print(f"Payload: {payload}")
response = requests.request("POST", url, json=payload, headers=headers)
parts_data = response.json()

for i in range(0, len(parts_data), batch_size):
    batch = parts_data[i:i + batch_size]

    # Calculate inventory value for each part in the batch
    for part_entry in batch:
        part = part_entry.get("part")
        part_number = part.get("mpn")
        inventory = part.get("stockBalance")

        print(f"Part Number: {part_number}")
        print(f"Stock Balance: {inventory}")
