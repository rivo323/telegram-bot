import os
import json
import time
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

DATA_FILE = "players.json"
offset = 0


# -------------------------
# Load players
# -------------------------

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            players = json.load(file)
    except:
        players = {}
else:
    players = {}


def save_players():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(players, file, ensure_ascii=False, indent=2)


def get_player(chat_id):
    chat_id = str(chat_id)

    if chat_id not in players:
        players[chat_id] = {
            "coins": 0,
            "power": 1
        }
        save_players()

    return players[chat_id]


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)

    requests.post(
        f"{API}/sendMessage",
        data=data
    )


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


# -------------------------
# Bot
# -------------------------

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

                save_players()

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

                    save_players()

                    send_message(
                        chat_id,
                        f"🚀 UPGRADE!\n\n"
                        f"⚡ Power: {player['power']}\n"
                        f"💰 Coins: {player['coins']}"
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

                save_players()

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

            else:

                send_message(
                    chat_id,
                    "💰 Welcome to Coin Rush!\n\n"
                    "Press 🪙 TAP! to earn coins."
                )

        time.sleep(1)

    except Exception as error:

        print("Error:", error)

        time.sleep(5)
