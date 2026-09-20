import os
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")

url = f"https://api.telegram.org/bot{TOKEN}/getMe"

response = requests.get(url)

print(response.json())
