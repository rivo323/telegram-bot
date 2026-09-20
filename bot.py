import os
import json
import time
import secrets
import requests
from datetime import datetime, timezone

# ============================================================
# COIN RUSH
# Telegram Game + Telegram Stars Monetization
# ============================================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID", "")

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")

API = f"https://api.telegram.org/bot{TOKEN}"

DATA_FILE = "players.json"

POLL_TIMEOUT = 25
TAP_COOLDOWN = 0.15
COMBO_TIMEOUT = 3
MAX_COMBO = 25

# ============================================================
# PRODUCTS
# ============================================================

PRODUCTS = {
    "energy_pack": {
        "title": "Energy Pack",
        "description": "Get 5,000 instant Coins.",
        "stars": 25,
        "type": "coins",
        "coins": 5000
    },

    "double_coins": {
        "title": "2x Coins - 24 Hours",
        "description": "Double your tap earnings for 24 hours.",
        "stars": 50,
        "type": "boost",
        "hours": 24,
        "multiplier": 2
    },

    "mega_boost": {
        "title": "Mega Boost - 7 Days",
        "description": "Triple your tap earnings for 7 days.",
        "stars": 150,
        "type": "boost",
        "hours": 24 * 7,
        "multiplier": 3
    },

    "premium_chest": {
        "title": "Premium Chest",
        "description": "A premium chest containing 100,000 Coins.",
        "stars": 250,
        "type": "coins",
        "coins": 100000
    },

    "vip": {
        "title": "VIP - 30 Days",
        "description": "VIP status, 5x tap multiplier and 500,000 Coins.",
        "stars": 500,
        "type": "vip",
        "days": 30,
        "coins": 500000
    }
}


# ============================================================
# BUSINESS SYSTEM
# ============================================================

BUSINESSES = {
    "lemonade": {
        "name": "🥤 Lemonade Stand",
        "price": 1000,
        "income": 5
    },

    "pizza": {
        "name": "🍕 Pizza Shop",
        "price": 10000,
        "income": 60
    },

    "market": {
        "name": "🏪 Supermarket",
        "price": 100000,
        "income": 500
    },

    "tower": {
        "name": "🏢 Business Tower",
        "price": 1000000,
        "income": 5000
    },

    "empire": {
        "name": "👑 Mega Empire",
        "price": 10000000,
        "income": 50000
    }
}


# ============================================================
# DATA
# ============================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "players": {},
            "payments": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("players", {})
        data.setdefault("payments", {})

        return data

    except Exception:
        return {
            "players": {},
            "payments": {}
        }


DATA = load_data()
players = DATA["players"]
payments = DATA["payments"]


def save_data():
    DATA["players"] = players
    DATA["payments"] = payments

    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            DATA,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_file, DATA_FILE)


# ============================================================
# PLAYER
# ============================================================

def create_player(user):
    now = time.time()

    return {
        "id": user["id"],
        "username": user.get("username", ""),
        "first_name": user.get("first_name", "Player"),

        "coins": 0,
        "power": 1,

        "total_taps": 0,
        "total_earned": 0,

        "combo": 0,
        "last_tap": 0,

        "last_daily": 0,

        "last_income": now,

        "referrals": 0,
        "referred_by": None,

        "businesses": {
            "lemonade": 0,
            "pizza": 0,
            "market": 0,
            "tower": 0,
            "empire": 0
        },

        "boost_multiplier": 1,
        "boost_until": 0,

        "vip_until": 0,

        "purchases": []
    }


def get_player(user):
    user_id = str(user["id"])

    if user_id not in players:
        players[user_id] = create_player(user)
        save_data()

    player = players[user_id]

    # Compatibility / defaults
    player.setdefault("coins", 0)
    player.setdefault("power", 1)
    player.setdefault("total_taps", 0)
    player.setdefault("total_earned", 0)
    player.setdefault("combo", 0)
    player.setdefault("last_tap", 0)
    player.setdefault("last_daily", 0)
    player.setdefault("last_income", time.time())
    player.setdefault("referrals", 0)
    player.setdefault("referred_by", None)
    player.setdefault("boost_multiplier", 1)
    player.setdefault("boost_until", 0)
    player.setdefault("vip_until", 0)
    player.setdefault("purchases", [])

    player.setdefault("businesses", {})

    for business_id in BUSINESSES:
        player["businesses"].setdefault(
            business_id,
            0
        )

    return player


# ============================================================
# TELEGRAM API
# ============================================================

def telegram(method, payload=None):

    try:
        response = requests.post(
            f"{API}/{method}",
            json=payload or {},
            timeout=30
        )

        result = response.json()

        if not result.get("ok"):
            print(
                "Telegram API error:",
                method,
                result
            )

        return result

    except Exception as e:
        print("Telegram request error:", method, e)
        return None


def send_message(chat_id, text, keyboard=None):

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    return telegram("sendMessage", payload)


# ============================================================
# KEYBOARDS
# ============================================================

def main_keyboard():

    return {
        "keyboard": [
            [{"text": "🪙 TAP!"}],
            [{"text": "🏪 Businesses"}, {"text": "⚡ Upgrade"}],
            [{"text": "🛍️ Shop"}, {"text": "🎁 Daily Reward"}],
            [{"text": "🏆 Leaderboard"}, {"text": "📊 Stats"}],
            [{"text": "👥 Invite Friends"}]
        ],
        "resize_keyboard": True
    }


def shop_keyboard():

    return {
        "keyboard": [
            [{"text": "⚡ Energy Pack"}],
            [{"text": "🚀 2x Coins - 24h"}],
            [{"text": "🔥 Mega Boost - 7 Days"}],
            [{"text": "🎁 Premium Chest"}],
            [{"text": "👑 VIP - 30 Days"}],
            [{"text": "🔙 Main Menu"}]
        ],
        "resize_keyboard": True
    }


def business_keyboard():

    return {
        "keyboard": [
            [{"text": "🥤 Buy Lemonade"}],
            [{"text": "🍕 Buy Pizza"}],
            [{"text": "🏪 Buy Supermarket"}],
            [{"text": "🏢 Buy Tower"}],
            [{"text": "👑 Buy Mega Empire"}],
            [{"text": "🔙 Main Menu"}]
        ],
        "resize_keyboard": True
    }


# ============================================================
# BOOSTS
# ============================================================

def active_multiplier(player):

    now = time.time()

    multiplier = 1

    if player.get("boost_until", 0) > now:
        multiplier = max(
            multiplier,
            player.get("boost_multiplier", 1)
        )

    if player.get("vip_until", 0) > now:
        multiplier = max(multiplier, 5)

    return multiplier


# ============================================================
# PASSIVE INCOME
# ============================================================

def income_per_minute(player):

    total = 0

    for business_id, business in BUSINESSES.items():

        amount = player["businesses"].get(
            business_id,
            0
        )

        if amount > 0:

            level_multiplier = (
                1 + ((amount - 1) * 0.10)
            )

            total += int(
                business["income"]
                * amount
                * level_multiplier
            )

    return int(total)


def collect_income(player):

    now = time.time()

    last_income = player.get(
        "last_income",
        now
    )

    elapsed = max(
        0,
        now - last_income
    )

    # Never calculate more than 24 hours at once
    elapsed = min(
        elapsed,
        24 * 60 * 60
    )

    rate = income_per_minute(player)

    earned = int(
        (elapsed / 60) * rate
    )

    player["last_income"] = now

    if earned > 0:

        player["coins"] += earned
        player["total_earned"] += earned

    return earned


# ============================================================
# MAIN MENU
# ============================================================

def show_main_menu(user):

    chat_id = user["id"]
    player = get_player(user)

    collect_income(player)
    save_data()

    multiplier = active_multiplier(player)

    send_message(
        chat_id,

        "💰 COIN RUSH\n\n"

        f"🪙 Coins: {player['coins']:,}\n"
        f"⚡ Power: {player['power']}\n"
        f"🔥 Combo: x{max(1, player['combo'])}\n"
        f"🚀 Multiplier: x{multiplier}\n\n"

        "Build your empire. Earn more. "
        "Climb the leaderboard. 🏆",

        main_keyboard()
    )


# ============================================================
# TAP
# ============================================================

def handle_tap(user):

    chat_id = user["id"]
    player = get_player(user)

    now = time.time()

    collect_income(player)

    if (
        now - player.get("last_tap", 0)
        < TAP_COOLDOWN
    ):
        return

    if (
        now - player.get("last_tap", 0)
        <= COMBO_TIMEOUT
    ):
        player["combo"] += 1

    else:
        player["combo"] = 1

    player["combo"] = min(
        player["combo"],
        MAX_COMBO
    )

    combo_multiplier = (
        1 + (player["combo"] * 0.10)
    )

    permanent_multiplier = active_multiplier(
        player
    )

    earned = int(
        player["power"]
        * combo_multiplier
        * permanent_multiplier
    )

    player["coins"] += earned
    player["total_earned"] += earned
    player["total_taps"] += 1
    player["last_tap"] = now

    save_data()

    combo_text = ""

    if player["combo"] >= 3:

        combo_text = (
            f"\n🔥 COMBO x{player['combo']}"
        )

    send_message(
        chat_id,

        f"🪙 +{earned:,} Coins!"
        f"{combo_text}\n\n"

        f"💰 Balance: {player['coins']:,}\n"
        f"⚡ Power: {player['power']}"
    )


# ============================================================
# POWER UPGRADE
# ============================================================

def upgrade_power(user):

    chat_id = user["id"]
    player = get_player(user)

    collect_income(player)

    price = player["power"] * 100

    if player["coins"] < price:

        send_message(
            chat_id,

            "❌ Not enough Coins.\n\n"
            f"⚡ Upgrade cost: {price:,}\n"
            f"🪙 Your balance: {player['coins']:,}"
        )

        return

    player["coins"] -= price
    player["power"] += 1

    save_data()

    send_message(
        chat_id,

        "🚀 POWER UPGRADED!\n\n"

        f"⚡ New Power: {player['power']}\n"
        f"💰 Coins: {player['coins']:,}"
    )


# ============================================================
# BUSINESSES
# ============================================================

def show_businesses(user):

    chat_id = user["id"]
    player = get_player(user)

    collect_income(player)

    text = (
        "🏪 YOUR BUSINESS EMPIRE\n\n"
        f"🪙 Coins: {player['coins']:,}\n\n"
    )

    for business_id, business in BUSINESSES.items():

        owned = player["businesses"].get(
            business_id,
            0
        )

        price = int(
            business["price"]
            * (1.65 ** owned)
        )

        current_income = int(
            business["income"]
            * owned
            * (
                1 + max(0, owned - 1) * 0.10
            )
        )

        text += (
            f"{business['name']}\n"
            f"Level: {owned}\n"
            f"Next: {price:,} Coins\n"
            f"Income: {current_income:,}/min\n\n"
        )

    text += (
        f"📈 Total passive income: "
        f"{income_per_minute(player):,}/min"
    )

    save_data()

    send_message(
        chat_id,
        text,
        business_keyboard()
    )


def buy_business(user, business_id):

    chat_id = user["id"]
    player = get_player(user)

    collect_income(player)

    business = BUSINESSES[business_id]

    owned = player["businesses"].get(
        business_id,
        0
    )

    price = int(
        business["price"]
        * (1.65 ** owned)
    )

    if player["coins"] < price:

        send_message(
            chat_id,

            "❌ You cannot afford this business yet.\n\n"

            f"{business['name']}\n"
            f"💰 Price: {price:,}\n"
            f"🪙 Your Coins: {player['coins']:,}"
        )

        return

    player["coins"] -= price

    player["businesses"][business_id] = (
        owned + 1
    )

    save_data()

    send_message(
        chat_id,

        "🎉 BUSINESS PURCHASED!\n\n"

        f"{business['name']}\n"
        f"🏪 Level: {owned + 1}\n\n"

        f"💰 Coins: {player['coins']:,}\n"
        f"📈 Passive income: "
        f"{income_per_minute(player):,}/min"
    )


# ============================================================
# DAILY REWARD
# ============================================================

def daily_reward(user):

    chat_id = user["id"]
    player = get_player(user)

    now = time.time()

    collect_income(player)

    if (
        now - player.get("last_daily", 0)
        < 24 * 60 * 60
    ):

        remaining = int(
            24 * 60 * 60
            - (
                now
                - player["last_daily"]
            )
        )

        hours = remaining // 3600
        minutes = (
            remaining % 3600
        ) // 60

        send_message(
            chat_id,

            "🎁 DAILY REWARD\n\n"
            "You already collected today's reward.\n\n"
            f"⏰ Come back in "
            f"{hours}h {minutes}m."
        )

        return

    reward = (
        500
        + income_per_minute(player) * 5
    )

    player["coins"] += reward
    player["total_earned"] += reward
    player["last_daily"] = now

    save_data()

    send_message(
        chat_id,

        "🎁 DAILY REWARD CLAIMED!\n\n"

        f"🪙 +{reward:,} Coins\n"
        f"💰 Balance: {player['coins']:,}\n\n"

        "Come back tomorrow! 🔥"
    )


# ============================================================
# LEADERBOARD
# ============================================================

def leaderboard(user):

    chat_id = user["id"]

    for player in players.values():
        collect_income(player)

    save_data()

    ranking = []

    for player_id, player in players.items():

        ranking.append({
            "id": player_id,
            "earned": player.get(
                "total_earned",
                0
            ),
            "power": player.get(
                "power",
                1
            ),
            "businesses": sum(
                player.get(
                    "businesses",
                    {}
                ).values()
            )
        })

    ranking.sort(
        key=lambda x: x["earned"],
        reverse=True
    )

    top = ranking[:10]

    text = (
        "🏆 COIN RUSH LEADERBOARD\n\n"
    )

    for index, item in enumerate(
        top,
        start=1
    ):

        marker = ""

        if item["id"] == str(chat_id):
            marker = " ⭐ YOU"

        text += (
            f"{index}. "
            f"🪙 {item['earned']:,} "
            f"| ⚡ {item['power']}"
            f"{marker}\n"
        )

    position = None

    for index, item in enumerate(
        ranking,
        start=1
    ):

        if item["id"] == str(chat_id):
            position = index
            break

    if position:
        text += (
            f"\n📍 Your position: #{position}"
        )

    send_message(
        chat_id,
        text
    )


# ============================================================
# STATS
# ============================================================

def show_stats(user):

    chat_id = user["id"]
    player = get_player(user)

    collect_income(player)

    multiplier = active_multiplier(player)

    businesses = sum(
        player["businesses"].values()
    )

    vip_active = (
        player.get("vip_until", 0)
        > time.time()
    )

    send_message(
        chat_id,

        "📊 YOUR STATS\n\n"

        f"🪙 Coins: {player['coins']:,}\n"
        f"⚡ Power: {player['power']}\n"
        f"🔥 Combo: x{max(1, player['combo'])}\n"
        f"🚀 Multiplier: x{multiplier}\n\n"

        f"👆 Total Taps: "
        f"{player['total_taps']:,}\n"

        f"💰 Total Earned: "
        f"{player['total_earned']:,}\n"

        f"🏪 Businesses: {businesses}\n"

        f"📈 Passive Income: "
        f"{income_per_minute(player):,}/min\n"

        f"👥 Referrals: "
        f"{player['referrals']}\n"

        f"👑 VIP: "
        f"{'ACTIVE' if vip_active else 'NO'}"
    )


# ============================================================
# REFERRALS
# ============================================================

def referral_link(user):

    bot_info = telegram("getMe")

    username = None

    if (
        bot_info
        and bot_info.get("ok")
    ):
        username = (
            bot_info["result"]
            .get("username")
        )

    if not username:

        send_message(
            user["id"],
            "Referral link is temporarily unavailable."
        )

        return

    link = (
        f"https://t.me/{username}"
        f"?start=ref_{user['id']}"
    )

    send_message(
        user["id"],

        "👥 INVITE FRIENDS\n\n"

        "Invite friends and earn Coins "
        "when they join.\n\n"

        f"🔗 Your referral link:\n{link}\n\n"

        "🎁 You receive 10,000 Coins "
        "for each eligible new player."
    )


def process_referral(user, start_parameter):

    if not start_parameter:
        return

    if not start_parameter.startswith("ref_"):
        return

    referrer_id = start_parameter[
        4:
    ]

    new_player_id = str(user["id"])

    if referrer_id == new_player_id:
        return

    player = get_player(user)

    # Never change an existing referrer
    if player.get("referred_by"):
        return

    if referrer_id not in players:
        return

    player["referred_by"] = referrer_id

    referrer = players[referrer_id]

    referrer["referrals"] = (
        referrer.get("referrals", 0)
        + 1
    )

    # Referral reward
    referrer["coins"] += 10000
    referrer["total_earned"] += 10000

    # New player gets a smaller welcome bonus
    player["coins"] += 2500
    player["total_earned"] += 2500

    save_data()

    try:

        send_message(
            int(referrer_id),

            "🎉 NEW REFERRAL!\n\n"
            "+10,000 Coins added to your account!"
        )

    except Exception:
        pass


# ============================================================
# SHOP
# ============================================================

def show_shop(user):

    player = get_player(user)

    collect_income(player)
    save_data()

    text = (
        "🛍️ COIN RUSH SHOP\n\n"

        "⭐ Buy premium boosts using "
        "Telegram Stars.\n\n"

        "⚡ Energy Pack — 25 ⭐\n"
        "5,000 Coins\n\n"

        "🚀 2x Coins — 24h — 50 ⭐\n\n"

        "🔥 Mega Boost — 7 Days — 150 ⭐\n\n"

        "🎁 Premium Chest — 250 ⭐\n"
        "100,000 Coins\n\n"

        "👑 VIP — 30 Days — 500 ⭐\n"
        "5x Tap multiplier + 500,000 Coins"
    )

    send_message(
        user["id"],
        text,
        shop_keyboard()
    )


# ============================================================
# PAYMENTS
# ============================================================

def send_invoice(user, product_id):

    if product_id not in PRODUCTS:
        return

    product = PRODUCTS[product_id]

    # Unique payload for this order
    order_id = secrets.token_urlsafe(12)

    payload = (
        f"coinrush:"
        f"{product_id}:"
        f"{user['id']}:"
        f"{order_id}"
    )

    payments[order_id] = {
        "user_id": str(user["id"]),
        "product_id": product_id,
        "stars": product["stars"],
        "status": "created",
        "created_at": time.time()
    }

    save_data()

    result = telegram(
        "sendInvoice",
        {
            "chat_id": user["id"],

            "title": product["title"],

            "description": product["description"],

            "payload": payload,

            "provider_token": "",

            "currency": "XTR",

            "prices": [
                {
                    "label": product["title"],
                    "amount": product["stars"]
                }
            ]
        }
    )

    if not result or not result.get("ok"):

        payments[order_id]["status"] = (
            "invoice_failed"
        )

        save_data()

        send_message(
            user["id"],
            "❌ Payment system error. "
            "Please try again later."
        )


# ============================================================
# PRE-CHECKOUT
# ============================================================

def handle_pre_checkout(query):

    query_id = query["id"]

    payload = query.get(
        "invoice_payload",
        ""
    )

    parts = payload.split(":")

    if len(parts) != 4:

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Invalid order."
            }
        )

        return

    _, product_id, user_id, order_id = parts

    if product_id not in PRODUCTS:

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Product is unavailable."
            }
        )

        return

    if order_id not in payments:

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Order not found."
            }
        )

        return

    order = payments[order_id]
    product = PRODUCTS[product_id]

    # Verify user
    if str(query["from"]["id"]) != str(user_id):

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "This order belongs to another user."
            }
        )

        return

    # Verify amount
    if query.get("total_amount") != product["stars"]:

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Incorrect payment amount."
            }
        )

        return

    # Everything is valid
    order["status"] = "approved"

    save_data()

    telegram(
        "answerPreCheckoutQuery",
        {
            "pre_checkout_query_id":
                query_id,

            "ok": True
        }
    )


# ============================================================
# SUCCESSFUL PAYMENT
# ============================================================

def handle_successful_payment(user, payment):

    user_id = str(user["id"])

    payload = payment.get(
        "invoice_payload",
        ""
    )

    charge_id = payment.get(
        "telegram_payment_charge_id"
    )

    total_amount = payment.get(
        "total_amount",
        0
    )

    parts = payload.split(":")

    if len(parts) != 4:
        return

    _, product_id, payload_user_id, order_id = parts

    # Security check
    if str(payload_user_id) != user_id:
        return

    if product_id not in PRODUCTS:
        return

    # Prevent duplicate delivery
    if charge_id in payments:

        existing = payments[charge_id]

        if existing.get("status") == "delivered":
            return

    if order_id not in payments:

        payments[order_id] = {
            "user_id": user_id,
            "product_id": product_id,
            "stars": total_amount,
            "status": "received",
            "created_at": time.time()
        }

    order = payments[order_id]

    if order.get("status") == "delivered":
        return

    player = get_player(user)

    product = PRODUCTS[product_id]

    # --------------------------------------------------------
    # DELIVER PRODUCT
    # --------------------------------------------------------

    if product["type"] == "coins":

        coins = product["coins"]

        player["coins"] += coins
        player["total_earned"] += coins

        confirmation = (
            "🎉 PURCHASE COMPLETE!\n\n"
            f"🪙 +{coins:,} Coins added!\n\n"
            f"💰 Balance: {player['coins']:,}"
        )

    elif product["type"] == "boost":

        duration = (
            product["hours"]
            * 60
            * 60
        )

        now = time.time()

        current_until = player.get(
            "boost_until",
            0
        )

        if current_until > now:
            player["boost_until"] = (
                current_until + duration
            )

        else:
            player["boost_until"] = (
                now + duration
            )

        player["boost_multiplier"] = max(
            player.get(
                "boost_multiplier",
                1
            ),
            product["multiplier"]
        )

        confirmation = (
            "🎉 PURCHASE COMPLETE!\n\n"
            f"🚀 x{product['multiplier']} "
            f"Coins Boost activated!\n\n"
            f"Duration: {product['hours']} hours."
        )

    elif product["type"] == "vip":

        duration = (
            product["days"]
            * 24
            * 60
            * 60
        )

        now = time.time()

        current_until = player.get(
            "vip_until",
            0
        )

        if current_until > now:
            player["vip_until"] = (
                current_until + duration
            )

        else:
            player["vip_until"] = (
                now + duration
            )

        coins = product["coins"]

        player["coins"] += coins
        player["total_earned"] += coins

        confirmation = (
            "👑 VIP ACTIVATED!\n\n"

            "⭐ VIP benefits:\n"
            "• 5x Tap multiplier\n"
            "• 500,000 Coins\n"
            "• VIP status for 30 days\n\n"

            f"🪙 +{coins:,} Coins"
        )

    else:
        confirmation = (
            "🎉 Purchase completed!"
        )

    # --------------------------------------------------------
    # RECORD PURCHASE
    # --------------------------------------------------------

    purchase = {
        "order_id": order_id,
        "charge_id": charge_id,
        "product_id": product_id,
        "stars": total_amount,
        "timestamp": time.time()
    }

    player["purchases"].append(purchase)

    order["status"] = "delivered"
    order["charge_id"] = charge_id
    order["delivered_at"] = time.time()

    # Store charge separately to prevent duplicates
    if charge_id:
        payments[charge_id] = {
            "status": "delivered",
            "user_id": user_id,
            "product_id": product_id,
            "stars": total_amount,
            "order_id": order_id,
            "delivered_at": time.time()
        }

    save_data()

    send_message(
        user["id"],
        confirmation
        + "\n\nThank you for supporting Coin Rush! ❤️"
    )


# ============================================================
# COMMANDS
# ============================================================

def show_terms(chat_id):

    send_message(
        chat_id,

        "📜 COIN RUSH TERMS\n\n"

        "Coins, boosts, VIP status and other "
        "game items are virtual digital items "
        "for use inside Coin Rush.\n\n"

        "They have no cash value and cannot "
        "be withdrawn or exchanged for real money.\n\n"

        "Purchases of digital items are processed "
        "using Telegram Stars.\n\n"

        "By using Coin Rush, you agree to use "
        "the service fairly and not attempt to "
        "exploit, manipulate or abuse the game."
    )


def show_privacy(chat_id):

    send_message(
        chat_id,

        "🔐 COIN RUSH PRIVACY\n\n"

        "Coin Rush stores information needed "
        "to operate the game, including your "
        "Telegram user ID, game progress, "
        "Coins, referrals and purchase records.\n\n"

        "Payment information is processed through "
        "Telegram's payment system.\n\n"

        "We do not ask you for your credit card "
        "details."
    )


def show_payment_support(chat_id):

    send_message(
        chat_id,

        "💳 PAYMENT SUPPORT\n\n"

        "If you have a problem with a purchase, "
        "please send:\n\n"

        "1. Your Telegram username\n"
        "2. Product name\n"
        "3. Approximate purchase time\n"
        "4. Telegram payment charge ID "
        "if available\n\n"

        "Support: contact the Coin Rush owner."
    )


# ============================================================
# ADMIN
# ============================================================

def is_admin(user_id):

    return (
        ADMIN_ID
        and str(user_id) == str(ADMIN_ID)
    )


def admin_stats(user):

    if not is_admin(user["id"]):

        send_message(
            user["id"],
            "⛔ Admin only."
        )

        return

    total_users = len(players)

    total_stars = 0
    delivered_orders = 0

    for payment in payments.values():

        if (
            payment.get("status")
            == "delivered"
        ):

            total_stars += int(
                payment.get("stars", 0)
            )

            delivered_orders += 1

    result = telegram(
        "getMyStarBalance"
    )

    telegram_balance = "Unknown"

    if result and result.get("ok"):

        telegram_balance = (
            result["result"]
            .get("amount", "Unknown")
        )

    send_message(
        user["id"],

        "👑 ADMIN DASHBOARD\n\n"

        f"👥 Users: {total_users}\n"
        f"💳 Delivered purchases: "
        f"{delivered_orders}\n"
        f"⭐ Recorded Stars: "
        f"{total_stars:,}\n"
        f"⭐ Current bot Star balance: "
        f"{telegram_balance}\n"
    )


# ============================================================
# START
# ============================================================

def handle_start(user, text):

    parameter = ""

    parts = text.split(
        maxsplit=1
    )

    if len(parts) == 2:
        parameter = parts[1].strip()

    is_new = (
        str(user["id"])
        not in players
    )

    player = get_player(user)

    if is_new and parameter:

        process_referral(
            user,
            parameter
        )

    show_main_menu(user)


# ============================================================
# MESSAGE ROUTER
# ============================================================

def handle_message(message):

    user = message.get("from")

    if not user:
        return

    text = message.get(
        "text",
        ""
    ).strip()

    player = get_player(user)

    collect_income(player)

    save_data()

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    if text.startswith("/start"):

        handle_start(
            user,
            text
        )

        return

    if text == "/help":

        show_main_menu(user)

        return

    if text == "/terms":

        show_terms(user["id"])

        return

    if text == "/privacy":

        show_privacy(user["id"])

        return

    if text == "/paysupport":

        show_payment_support(
            user["id"]
        )

        return

    if text == "/admin":

        admin_stats(user)

        return

    # --------------------------------------------------------
    # GAME
    # --------------------------------------------------------

    if text == "🪙 TAP!":

        handle_tap(user)

        return

    if text == "⚡ Upgrade":

        upgrade_power(user)

        return

    if text == "🏪 Businesses":

        show_businesses(user)

        return

    # --------------------------------------------------------
    # BUSINESSES
    # --------------------------------------------------------

    business_buttons = {
        "🥤 Buy Lemonade": "lemonade",
        "🍕 Buy Pizza": "pizza",
        "🏪 Buy Supermarket": "market",
        "🏢 Buy Tower": "tower",
        "👑 Buy Mega Empire": "empire"
    }

    if text in business_buttons:

        buy_business(
            user,
            business_buttons[text]
        )

        return

    # --------------------------------------------------------
    # DAILY
    # --------------------------------------------------------

    if text == "🎁 Daily Reward":

        daily_reward(user)

        return

    # --------------------------------------------------------
    # LEADERBOARD
    # --------------------------------------------------------

    if text == "🏆 Leaderboard":

        leaderboard(user)

        return

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    if text == "📊 Stats":

        show_stats(user)

        return

    # --------------------------------------------------------
    # REFERRALS
    # --------------------------------------------------------

    if text == "👥 Invite Friends":

        referral_link(user)

        return

    # --------------------------------------------------------
    # SHOP
    # --------------------------------------------------------

    if text == "🛍️ Shop":

        show_shop(user)

        return

    product_buttons = {
        "⚡ Energy Pack": "energy_pack",
        "🚀 2x Coins - 24h": "double_coins",
        "🔥 Mega Boost - 7 Days": "mega_boost",
        "🎁 Premium Chest": "premium_chest",
        "👑 VIP - 30 Days": "vip"
    }

    if text in product_buttons:

        send_invoice(
            user,
            product_buttons[text]
        )

        return

    # --------------------------------------------------------
    # MAIN MENU
    # --------------------------------------------------------

    if text == "🔙 Main Menu":

        show_main_menu(user)

        return


# ============================================================
# UPDATE PROCESSOR
# ============================================================

def process_update(update):

    # Normal message
    if update.get("message"):

        message = update["message"]

        # Successful payment is a message service object
        if message.get("successful_payment"):

            user = message.get("from")

            payment = message[
                "successful_payment"
            ]

            handle_successful_payment(
                user,
                payment
            )

            return

        handle_message(message)

        return

    # Pre-checkout
    if update.get(
        "pre_checkout_query"
    ):

        handle_pre_checkout(
            update[
                "pre_checkout_query"
            ]
        )

        return


# ============================================================
# BOT LOOP
# ============================================================

def main():

    offset = 0

    print("🚀 Coin Rush is running!")

    print(
        "💰 Telegram Stars payments enabled."
    )

    while True:

        try:

            result = telegram(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": POLL_TIMEOUT,
                    "allowed_updates": [
                        "message",
                        "pre_checkout_query"
                    ]
                }
            )

            if not result:
                time.sleep(2)
                continue

            if not result.get("ok"):
                time.sleep(3)
                continue

            for update in result.get(
                "result",
                []
            ):

                offset = (
                    update["update_id"] + 1
                )

                try:

                    process_update(update)

                except Exception as e:

                    print(
                        "Update error:",
                        e
                    )

        except KeyboardInterrupt:

            print(
                "Coin Rush stopped."
            )

            break

        except Exception as e:

            print(
                "Main loop error:",
                e
            )

            time.sleep(5)


if __name__ == "__main__":
    main()
