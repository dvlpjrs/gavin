import requests
from decouple import config


def fetch_data(query):
    headers = {"x-api-key": config("JIGSAW_API_KEY")}
    url = f"https://api.jigsawstack.com/v1/web/search?query='{query}'"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return {"error": "Failed to fetch data", "status_code": response.status_code}


# Example usage
query = "Time Square New York"
data = fetch_data(query)
print(data)
