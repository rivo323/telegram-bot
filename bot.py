import os
import requests
import time

TOKEN = os.environ.get("TELEGRAM_TOKEN")

offset = 0

while True:
    response = requests.get(
        f"https://api.telegram.org/bot{TOKEN}/getUpdates",
        params={"offset": offset, "timeout": 20}
    )

    data = response.json()

    for update in data.get("result", []):
        offset = update["update_id"] + 1

        message = update.get("message")

        if message and message.get("text") == "/start":
            chat_id = message["chat"]["id"]

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": "היי ❤️ הבוט עובד!"
                }
            )

    time.sleep(1)
