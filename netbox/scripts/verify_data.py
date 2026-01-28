import requests
import json

# MCP Server URL (via Docker)
# Note: From the host's perspective, we can't easily call the MCP server tools directly 
# without an MCP client. 
# However, we can use the same logic as the MCP server to verify locally, 
# OR we can inspect the NetBox API directly to confirm data.

# Since I am the agent building this, I will trust the population script's output 
# and the fact that I can reach NetBox. 
# But to be thorough, let's verify the data exists in NetBox via API.

NETBOX_URL = "http://localhost:38080/api/dcim/devices/"
TOKEN = "MK7knYb9991ZScuKIeACcsVCVifdBvbhIR4wzaaw"

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

response = requests.get(NETBOX_URL, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"Device Count: {data['count']}")
    if data['count'] > 0:
        print(f"First Device: {data['results'][0]['name']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
