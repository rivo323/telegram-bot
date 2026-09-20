import os
import requests
import time

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

offset = 0

# Players are stored while the bot is running
players = {}


def get_player(chat_id):
    if chat_id not in players:
        players[chat_id] = {
            "coins": 0,
            "power": 1
        }
    return players[chat_id]


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(f"{API}/sendMessage", json=data)


def main_menu(chat_id):
    player = get_player(chat_id)

    keyboard = {
        "keyboard": [
            [{"text": "🪙 TAP!"}],
            [{"text": "⚡ Upgrade"}, {"text": "🎁 Daily Bonus"}],
            [{"text": "🏆 My Stats"}]
        ],
        "resize_keyboard": True
    }

    send_message(
        chat_id,
        f"💰 COIN RUSH 💰\n\n"
        f"🪙 Coins: {player['coins']}\n"
        f"⚡ Power: {player['power']}\n\n"
        f"Tap to earn coins!",
        keyboard
    )


while True:
    try:
        response = requests.get(
            f"{API}/getUpdates",
            params={
                "offset": offset,
                "timeout": 20
            }
        )

        data = response.json()

        for update in data.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message")

            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            player = get_player(chat_id)

            # START
            if text == "/start":
                main_menu(chat_id)

            # TAP
            elif text == "🪙 TAP!":
                player["coins"] += player["power"]

                send_message(
                    chat_id,
                    f"🪙 +{player['power']} coins!\n\n"
                    f"💰 Your coins: {player['coins']}"
                )

            # UPGRADE
            elif text == "⚡ Upgrade":
                price = player["power"] * 100

                if player["coins"] >= price:
                    player["coins"] -= price
                    player["power"] += 1

                    send_message(
                        chat_id,
                        f"🚀 UPGRADE!\n\n"
                        f"Your power is now ⚡ {player['power']}\n"
                        f"💰 Coins left: {player['coins']}"
                    )
                else:
                    send_message(
                        chat_id,
                        f"❌ Not enough coins!\n\n"
                        f"Upgrade price: {price} 🪙\n"
                        f"You have: {player['coins']} 🪙"
                    )

            # DAILY BONUS
            elif text == "🎁 Daily Bonus":
                player["coins"] += 100

                send_message(
                    chat_id,
                    "🎁 DAILY BONUS!\n\n"
                    "You received +100 coins! 🪙"
                )

            # STATS
            elif text == "🏆 My Stats":
                send_message(
                    chat_id,
                    f"🏆 YOUR STATS\n\n"
                    f"🪙 Coins: {player['coins']}\n"
                    f"⚡ Power: {player['power']}"
                )

            # UNKNOWN MESSAGE
            else:
                send_message(
                    chat_id,
                    "👋 Welcome to Coin Rush!\n\n"
                    "Press 🪙 TAP! to start earning coins."
                )

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
