import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NEWS_API_KEY")

url = "https://newsapi.org/v2/everything"
params = {
    "q": "JCDecaux",
    "apiKey": api_key,
    "pageSize": 3,
    "sortBy": "publishedAt"
}

response = requests.get(url, params=params)
data = response.json()

if response.status_code != 200:
    print("Error:", data)
else:
    for article in data.get("articles", []):
        print("-", article["title"])