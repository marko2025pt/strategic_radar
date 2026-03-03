import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

params = {
    "function": "OVERVIEW",
    "symbol": "CCO",
    "apikey": API_KEY
}

response = requests.get("https://www.alphavantage.co/query", params=params)
print(response.json())