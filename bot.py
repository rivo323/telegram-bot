import os
import json
import time
import requests

# ============================================================
# COIN RUSH
# Complete Telegram Game Bot
# ============================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")

API_URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = "players.json"

# ============================================================
# GAME SETTINGS
# ============================================================

TAP_COOLDOWN = 0.35

DAILY_REWARD = 500

UPGRADE_BASE_COST = 100

REFERRER_REWARD = 10_000
NEW_PLAYER_REWARD = 2_500

# ============================================================
# BUSINESSES
# ============================================================

BUSINESSES = {
    "lemonade": {
        "name": "🍋 Lemonade Stand",
        "price": 1_000,
        "income": 5
    },

    "pizza": {
        "name": "🍕 Pizza Shop",
        "price": 10_000,
        "income": 60
    },

    "market": {
        "name": "🛒 Supermarket",
        "price": 100_000,
        "income": 500
    },

    "tower": {
        "name": "🏢 Business Tower",
        "price": 1_000_000,
        "income": 5_000
    },

    "empire": {
        "name": "👑 Mega Empire",
        "price": 10_000_000,
        "income": 50_000
    }
}

# ============================================================
# PREMIUM PRODUCTS
# Telegram Stars
# ============================================================

PRODUCTS = {

    "energy": {
        "title": "⚡ Energy Pack",
        "description": "Instantly receive 2,500 Coins.",
        "stars": 25
    },

    "double": {
        "title": "🔥 2x Coins",
        "description": "Double your tap rewards for 24 hours.",
        "stars": 50
    },

    "mega": {
        "title": "🚀 Mega Boost",
        "description": "Triple your tap rewards for 7 days.",
        "stars": 150
    },

    "chest": {
        "title": "🎁 Premium Chest",
        "description": "Receive 50,000 Coins instantly.",
        "stars": 250
    },

    "vip": {
        "title": "👑 VIP",
        "description": "VIP status for 30 days with bonus rewards.",
        "stars": 500
    }
}

# ============================================================
# STORAGE
# ============================================================

def load_players():

    if not os.path.exists(DATA_FILE):
        return {}

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:

        print("Could not load players:", error)

        return {}


players = load_players()


def save_players():

    try:

        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                players,
                file,
                indent=2,
                ensure_ascii=False
            )

    except Exception as error:

        print("Could not save players:", error)


# ============================================================
# TELEGRAM API
# ============================================================

def telegram(method, data=None):

    try:

        response = requests.post(
            f"{API_URL}/{method}",
            json=data or {},
            timeout=35
        )

        result = response.json()

        if not result.get("ok"):

            print(
                "Telegram API error:",
                method,
                result
            )

        return result

    except Exception as error:

        print(
            "Telegram request error:",
            method,
            error
        )

        return None


# ============================================================
# SEND MESSAGE
# ============================================================

def send_message(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:

        data["reply_markup"] = {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "is_persistent": True
        }

    return telegram(
        "sendMessage",
        data
    )


# ============================================================
# MAIN KEYBOARD
# ============================================================

MAIN_KEYBOARD = [

    ["🪙 Tap", "🎁 Daily Bonus"],

    ["⚡ Upgrade", "🏢 Businesses"],

    ["🛍 Shop", "🏆 My Stats"],

    ["🏅 Leaderboard", "👥 Referral"]

]


# ============================================================
# PLAYER CREATION
# ============================================================

def create_player(user):

    user_id = str(user["id"])

    if user_id not in players:

        players[user_id] = {

            "id": user["id"],

            "username": user.get(
                "username",
                ""
            ),

            "first_name": user.get(
                "first_name",
                "Player"
            ),

            "coins": 0,

            "power": 1,

            "total_taps": 0,

            "total_earned": 0,

            "last_tap": 0,

            "last_daily": 0,

            "last_income": time.time(),

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

            "purchases": 0,

            "payment_ids": []

        }

    else:

        player = players[user_id]

        player["username"] = user.get(
            "username",
            player.get("username", "")
        )

        player["first_name"] = user.get(
            "first_name",
            player.get("first_name", "Player")
        )

        # Safety for old players
        player.setdefault("coins", 0)
        player.setdefault("power", 1)
        player.setdefault("total_taps", 0)
        player.setdefault("total_earned", 0)
        player.setdefault("last_tap", 0)
        player.setdefault("last_daily", 0)
        player.setdefault("last_income", time.time())
        player.setdefault("referrals", 0)
        player.setdefault("referred_by", None)
        player.setdefault("boost_multiplier", 1)
        player.setdefault("boost_until", 0)
        player.setdefault("vip_until", 0)
        player.setdefault("purchases", 0)
        player.setdefault("payment_ids", [])

        player.setdefault(
            "businesses",
            {
                "lemonade": 0,
                "pizza": 0,
                "market": 0,
                "tower": 0,
                "empire": 0
            }
        )

    return players[user_id]


# ============================================================
# VIP / BOOST
# ============================================================

def update_boosts(player):

    now = time.time()

    if (
        player.get("boost_until", 0) > 0
        and now >= player["boost_until"]
    ):

        player["boost_multiplier"] = 1
        player["boost_until"] = 0


def current_multiplier(player):

    update_boosts(player)

    multiplier = player.get(
        "boost_multiplier",
        1
    )

    if player.get("vip_until", 0) > time.time():

        multiplier *= 1.25

    return multiplier


# ============================================================
# PASSIVE INCOME
# ============================================================

def collect_passive_income(player):

    now = time.time()

    last_income = player.get(
        "last_income",
        now
    )

    elapsed = now - last_income

    if elapsed < 60:

        return 0

    minutes = int(
        elapsed // 60
    )

    income_per_minute = 0

    for key, business in BUSINESSES.items():

        owned = player["businesses"].get(
            key,
            0
        )

        income_per_minute += (
            owned * business["income"]
        )

    if income_per_minute <= 0:

        player["last_income"] = now

        return 0

    earned = (
        minutes *
        income_per_minute
    )

    player["coins"] += earned

    player["total_earned"] += earned

    player["last_income"] = now

    return earned


# ============================================================
# TAP
# ============================================================

def tap(chat_id, player):

    now = time.time()

    collect_passive_income(player)

    last_tap = player.get(
        "last_tap",
        0
    )

    if now - last_tap < TAP_COOLDOWN:

        return

    multiplier = current_multiplier(
        player
    )

    reward = int(
        player["power"] *
        multiplier
    )

    if reward < 1:
        reward = 1

    player["coins"] += reward

    player["total_earned"] += reward

    player["total_taps"] += 1

    player["last_tap"] = now

    save_players()

    send_message(

        chat_id,

        f"🪙 +{reward:,} Coins!\n\n"
        f"💰 Balance: {player['coins']:,}\n"
        f"⚡ Power: {player['power']}\n"
        f"🔥 Multiplier: x{multiplier:g}"

    )


# ============================================================
# DAILY BONUS
# ============================================================

def daily_bonus(chat_id, player):

    collect_passive_income(player)

    now = time.time()

    last_daily = player.get(
        "last_daily",
        0
    )

    cooldown = 24 * 60 * 60

    if now - last_daily < cooldown:

        remaining = int(
            cooldown -
            (now - last_daily)
        )

        hours = remaining // 3600

        minutes = (
            remaining % 3600
        ) // 60

        send_message(

            chat_id,

            f"⏳ DAILY BONUS\n\n"
            f"You already claimed today's reward.\n\n"
            f"Come back in "
            f"{hours}h {minutes}m."

        )

        return

    reward = DAILY_REWARD

    if player.get("vip_until", 0) > now:

        reward *= 2

    player["coins"] += reward

    player["total_earned"] += reward

    player["last_daily"] = now

    save_players()

    send_message(

        chat_id,

        f"🎁 DAILY BONUS!\n\n"
        f"🪙 +{reward:,} Coins\n\n"
        f"💰 Balance: "
        f"{player['coins']:,}\n\n"
        f"Come back tomorrow! 🚀"

    )


# ============================================================
# UPGRADE
# ============================================================

def upgrade(chat_id, player):

    collect_passive_income(player)

    power = player.get(
        "power",
        1
    )

    cost = power * UPGRADE_BASE_COST

    if player["coins"] < cost:

        send_message(

            chat_id,

            f"❌ Not enough Coins.\n\n"
            f"⚡ Upgrade cost: "
            f"{cost:,}\n"
            f"🪙 Your balance: "
            f"{player['coins']:,}\n\n"
            f"Keep tapping to earn more!"

        )

        return

    player["coins"] -= cost

    player["power"] += 1

    save_players()

    send_message(

        chat_id,

        f"🎉 UPGRADE COMPLETE!\n\n"
        f"⚡ New Power: "
        f"{player['power']}\n\n"
        f"🪙 Coins per tap: "
        f"{player['power']}\n\n"
        f"💰 Balance: "
        f"{player['coins']:,}"

    )


# ============================================================
# BUSINESS MENU
# ============================================================

def businesses_menu(chat_id, player):

    collect_passive_income(player)

    text = "🏢 BUSINESS EMPIRE\n\n"

    for key, business in BUSINESSES.items():

        owned = player[
            "businesses"
        ].get(
            key,
            0
        )

        price = int(
            business["price"] *
            (1.65 ** owned)
        )

        income = (
            owned *
            business["income"]
        )

        text += (

            f"{business['name']}\n"
            f"🏢 Owned: {owned}\n"
            f"📈 Income: "
            f"+{income:,}/min\n"
            f"💰 Next price: "
            f"{price:,} Coins\n\n"

        )

    keyboard = [

        ["🍋 Lemonade Stand"],

        ["🍕 Pizza Shop"],

        ["🛒 Supermarket"],

        ["🏢 Business Tower"],

        ["👑 Mega Empire"],

        ["🔙 Main Menu"]

    ]

    send_message(
        chat_id,
        text,
        keyboard
    )


# ============================================================
# BUY BUSINESS
# ============================================================

def buy_business(
    chat_id,
    player,
    key
):

    collect_passive_income(player)

    business = BUSINESSES[key]

    owned = player[
        "businesses"
    ].get(
        key,
        0
    )

    price = int(
        business["price"] *
        (1.65 ** owned)
    )

    if player["coins"] < price:

        send_message(

            chat_id,

            f"❌ NOT ENOUGH COINS\n\n"
            f"{business['name']}\n\n"
            f"💰 Price: "
            f"{price:,}\n"
            f"🪙 Balance: "
            f"{player['coins']:,}\n\n"
            f"Keep tapping or buy a boost!"

        )

        return

    player["coins"] -= price

    player["businesses"][key] = (
        owned + 1
    )

    save_players()

    new_level = owned + 1

    new_income = (
        new_level *
        business["income"]
    )

    send_message(

        chat_id,

        f"🎉 BUSINESS PURCHASED!\n\n"
        f"{business['name']}\n\n"
        f"🏢 Level: "
        f"{new_level}\n"
        f"📈 Income: "
        f"+{new_income:,}/min\n\n"
        f"💰 Paid: "
        f"{price:,}\n"
        f"🪙 Balance: "
        f"{player['coins']:,}"

    )


# ============================================================
# STATS
# ============================================================

def stats(chat_id, player):

    passive = collect_passive_income(
        player
    )

    total_businesses = sum(
        player["businesses"].values()
    )

    income_per_minute = 0

    for key, business in BUSINESSES.items():

        income_per_minute += (
            player["businesses"].get(
                key,
                0
            )
            *
            business["income"]
        )

    multiplier = current_multiplier(
        player
    )

    vip = (
        "ACTIVE 👑"
        if player.get("vip_until", 0)
        > time.time()
        else "Not active"
    )

    send_message(

        chat_id,

        f"🏆 MY STATS\n\n"

        f"👤 {player['first_name']}\n\n"

        f"🪙 Coins: "
        f"{player['coins']:,}\n"

        f"⚡ Power: "
        f"{player['power']}\n"

        f"🔥 Multiplier: "
        f"x{multiplier:g}\n\n"

        f"👆 Total taps: "
        f"{player['total_taps']:,}\n"

        f"💰 Total earned: "
        f"{player['total_earned']:,}\n\n"

        f"🏢 Businesses: "
        f"{total_businesses}\n"

        f"📈 Passive income: "
        f"{income_per_minute:,}/min\n\n"

        f"👥 Referrals: "
        f"{player['referrals']}\n"

        f"👑 VIP: {vip}"

    )

    save_players()


# ============================================================
# LEADERBOARD
# ============================================================

def leaderboard(chat_id):

    if not players:

        send_message(
            chat_id,
            "🏅 No players yet."
        )

        return

    ranking = sorted(

        players.values(),

        key=lambda p:
        p.get(
            "total_earned",
            0
        ),

        reverse=True

    )

    text = "🏅 LEADERBOARD\n\n"

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for index, player in enumerate(
        ranking[:10],
        start=1
    ):

        name = (
            player.get("username")
            or player.get("first_name")
            or "Player"
        )

        earned = player.get(
            "total_earned",
            0
        )

        if index <= 3:

            prefix = medals[index - 1]

        else:

            prefix = f"{index}."

        text += (
            f"{prefix} "
            f"{name} — "
            f"{earned:,} Coins\n"
        )

    send_message(
        chat_id,
        text
    )


# ============================================================
# REFERRAL
# ============================================================

def referral(chat_id, player):

    result = telegram(
        "getMe"
    )

    if not result or not result.get("ok"):

        send_message(
            chat_id,
            "❌ Could not create referral link."
        )

        return

    username = result[
        "result"
    ]["username"]

    link = (
        f"https://t.me/"
        f"{username}"
        f"?start=ref_{player['id']}"
    )

    send_message(

        chat_id,

        f"👥 REFERRAL PROGRAM\n\n"

        f"Invite friends to Coin Rush!\n\n"

        f"🎁 You receive: "
        f"{REFERRER_REWARD:,} Coins\n"

        f"🎁 Friend receives: "
        f"{NEW_PLAYER_REWARD:,} Coins\n\n"

        f"🔗 YOUR LINK:\n"
        f"{link}"

    )


# ============================================================
# SHOP MENU
# ============================================================

def shop(chat_id, player):

    text = (
        "🛍 COIN RUSH SHOP\n\n"
        "Buy premium items with Telegram Stars ⭐\n\n"
    )

    for key, product in PRODUCTS.items():

        text += (
            f"{product['title']}\n"
            f"{product['description']}\n"
            f"⭐ {product['stars']} Stars\n\n"
        )

    keyboard = [

        ["⚡ Energy Pack"],

        ["🔥 2x Coins — 24h"],

        ["🚀 Mega Boost — 7 Days"],

        ["🎁 Premium Chest"],

        ["👑 VIP — 30 Days"],

        ["🔙 Main Menu"]

    ]

    send_message(
        chat_id,
        text,
        keyboard
    )


# ============================================================
# SEND STAR INVOICE
# ============================================================

def send_invoice(
    chat_id,
    product_key
):

    product = PRODUCTS.get(
        product_key
    )

    if not product:

        send_message(
            chat_id,
            "❌ Product not found."
        )

        return

    payload = (
        f"coinrush:"
        f"{product_key}:"
        f"{int(time.time())}"
    )

    data = {

        "chat_id": chat_id,

        "title": product["title"],

        "description":
            product["description"],

        "payload": payload,

        "provider_token": "",

        "currency": "XTR",

        "prices": [

            {
                "label":
                    product["title"],

                "amount":
                    product["stars"]
            }

        ]

    }

    result = telegram(
        "sendInvoice",
        data
    )

    if not result or not result.get("ok"):

        send_message(

            chat_id,

            "❌ Could not create payment.\n"
            "Please try again."

        )


# ============================================================
# PAYMENT PRODUCT BUTTONS
# ============================================================

def handle_shop_button(
    chat_id,
    text
):

    if text == "⚡ Energy Pack":

        send_invoice(
            chat_id,
            "energy"
        )

    elif text == "🔥 2x Coins — 24h":

        send_invoice(
            chat_id,
            "double"
        )

    elif text == "🚀 Mega Boost — 7 Days":

        send_invoice(
            chat_id,
            "mega"
        )

    elif text == "🎁 Premium Chest":

        send_invoice(
            chat_id,
            "chest"
        )

    elif text == "👑 VIP — 30 Days":

        send_invoice(
            chat_id,
            "vip"
        )


# ============================================================
# DELIVER PURCHASE
# ============================================================

def deliver_purchase(
    chat_id,
    player,
    product_key
):

    now = time.time()

    if product_key == "energy":

        amount = 2_500

        player["coins"] += amount

        player["total_earned"] += amount

        message = (
            "⚡ ENERGY PACK ACTIVATED!\n\n"
            f"🪙 +{amount:,} Coins\n\n"
            f"💰 Balance: "
            f"{player['coins']:,}"
        )

    elif product_key == "double":

        player[
            "boost_multiplier"
        ] = 2

        player[
            "boost_until"
        ] = now + (
            24 * 60 * 60
        )

        message = (
            "🔥 2x COINS ACTIVATED!\n\n"
            "Your tap rewards are doubled "
            "for 24 hours."
        )

    elif product_key == "mega":

        player[
            "boost_multiplier"
        ] = 3

        player[
            "boost_until"
        ] = now + (
            7 * 24 * 60 * 60
        )

        message = (
            "🚀 MEGA BOOST ACTIVATED!\n\n"
            "Your tap rewards are tripled "
            "for 7 days."
        )

    elif product_key == "chest":

        amount = 50_000

        player["coins"] += amount

        player["total_earned"] += amount

        message = (
            "🎁 PREMIUM CHEST OPENED!\n\n"
            f"🪙 +{amount:,} Coins\n\n"
            f"💰 Balance: "
            f"{player['coins']:,}"
        )

    elif product_key == "vip":

        player["vip_until"] = max(

            player.get(
                "vip_until",
                0
            ),

            now

        ) + (
            30 * 24 * 60 * 60
        )

        message = (
            "👑 VIP ACTIVATED!\n\n"
            "VIP is active for 30 days.\n\n"
            "🎁 Daily rewards are boosted.\n"
            "🔥 Tap rewards receive a VIP bonus."
        )

    else:

        message = (
            "❌ Unknown product."
        )

    player["purchases"] += 1

    save_players()

    send_message(
        chat_id,
        message
    )


# ============================================================
# PRE-CHECKOUT
# ============================================================

def handle_pre_checkout(
    query
):

    query_id = query["id"]

    payload = query.get(
        "invoice_payload",
        ""
    )

    currency = query.get(
        "currency",
        ""
    )

    if currency != "XTR":

        telegram(

            "answerPreCheckoutQuery",

            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "This payment must use Telegram Stars."

            }

        )

        return

    if not payload.startswith(
        "coinrush:"
    ):

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

    parts = payload.split(":")

    if len(parts) < 2:

        telegram(

            "answerPreCheckoutQuery",

            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Invalid product."

            }

        )

        return

    product_key = parts[1]

    if product_key not in PRODUCTS:

        telegram(

            "answerPreCheckoutQuery",

            {
                "pre_checkout_query_id":
                    query_id,

                "ok": False,

                "error_message":
                    "Product unavailable."

            }

        )

        return

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

def handle_successful_payment(
    chat_id,
    user,
    payment
):

    player = create_player(
        user
    )

    charge_id = payment.get(
        "telegram_payment_charge_id"
    )

    payload = payment.get(
        "invoice_payload",
        ""
    )

    # Prevent duplicate delivery
    if charge_id in player[
        "payment_ids"
    ]:

        send_message(

            chat_id,

            "ℹ️ This payment was "
            "already delivered."

        )

        return

    if not payload.startswith(
        "coinrush:"
    ):

        return

    parts = payload.split(":")

    if len(parts) < 2:

        return

    product_key = parts[1]

    if product_key not in PRODUCTS:

        return

    # Record BEFORE delivery
    # so repeated updates cannot double-credit
    player[
        "payment_ids"
    ].append(charge_id)

    deliver_purchase(
        chat_id,
        player,
        product_key
    )

    save_players()


# ============================================================
# HELP
# ============================================================

def show_help(chat_id):

    send_message(

        chat_id,

        "🎮 COIN RUSH HELP\n\n"

        "🪙 TAP\n"
        "Earn Coins by tapping.\n\n"

        "🎁 DAILY BONUS\n"
        "Claim a free reward every 24 hours.\n\n"

        "⚡ UPGRADE\n"
        "Increase the Coins you earn per tap.\n\n"

        "🏢 BUSINESSES\n"
        "Buy businesses and generate passive income.\n\n"

        "🛍 SHOP\n"
        "Purchase premium digital items using "
        "Telegram Stars ⭐.\n\n"

        "🏆 MY STATS\n"
        "See your progress.\n\n"

        "🏅 LEADERBOARD\n"
        "Compete with other players.\n\n"

        "👥 REFERRAL\n"
        "Invite friends and earn in-game Coins.\n\n"

        "🪙 Coins are virtual in-game currency "
        "and are not cashable."

    )


# ============================================================
# START
# ============================================================

def start_command(
    chat_id,
    user,
    args
):

    user_id = str(
        user["id"]
    )

    is_new = (
        user_id not in players
    )

    player = create_player(
        user
    )

    # --------------------------------------------------------
    # Referral
    # --------------------------------------------------------

    if is_new and args.startswith(
        "ref_"
    ):

        referrer_id = (
            args[4:].strip()
        )

        if (

            referrer_id
            and
            referrer_id != user_id
            and
            referrer_id in players
            and
            not player.get(
                "referred_by"
            )

        ):

            player[
                "referred_by"
            ] = referrer_id

            players[
                referrer_id
            ]["referrals"] += 1

            players[
                referrer_id
            ]["coins"] += (
                REFERRER_REWARD
            )

            players[
                referrer_id
            ]["total_earned"] += (
                REFERRER_REWARD
            )

            player["coins"] += (
                NEW_PLAYER_REWARD
            )

            player["total_earned"] += (
                NEW_PLAYER_REWARD
            )

    save_players()

    send_message(

        chat_id,

        f"🎮 WELCOME TO COIN RUSH!\n\n"

        f"Hey "
        f"{player['first_name']}! 👋\n\n"

        f"🪙 Tap to earn Coins.\n"
        f"⚡ Upgrade your power.\n"
        f"🏢 Build your business empire.\n"
        f"🏆 Climb the leaderboard.\n"
        f"👥 Invite friends.\n"
        f"⭐ Buy premium boosts.\n\n"

        f"Let's get rich in the game! 🚀",

        MAIN_KEYBOARD

    )


# ============================================================
# COMMANDS
# ============================================================

def handle_command(
    chat_id,
    user,
    text
):

    parts = text.split()

    command = (
        parts[0]
        .split("@")[0]
        .lower()
    )

    args = ""

    if len(parts) > 1:

        args = " ".join(
            parts[1:]
        )

    if command == "/start":

        start_command(
            chat_id,
            user,
            args
        )

    elif command == "/help":

        show_help(
            chat_id
        )

    elif command == "/stats":

        player = create_player(
            user
        )

        stats(
            chat_id,
            player
        )

    elif command == "/leaderboard":

        leaderboard(
            chat_id
        )

    elif command == "/shop":

        player = create_player(
            user
        )

        shop(
            chat_id,
            player
        )

    elif command == "/referral":

        player = create_player(
            user
        )

        referral(
            chat_id,
            player
        )

    else:

        send_message(

            chat_id,

            "❓ Unknown command.\n\n"
            "Use /help.",

            MAIN_KEYBOARD

        )


# ============================================================
# TEXT HANDLER
# ============================================================

def handle_text(
    chat_id,
    user,
    text
):

    player = create_player(
        user
    )

    text = text.strip()

    # ========================================================
    # MAIN MENU
    # ========================================================

    if text == "🪙 Tap":

        tap(
            chat_id,
            player
        )

    elif text == "🎁 Daily Bonus":

        daily_bonus(
            chat_id,
            player
        )

    elif text == "⚡ Upgrade":

        upgrade(
            chat_id,
            player
        )

    elif text == "🏢 Businesses":

        businesses_menu(
            chat_id,
            player
        )

    elif text == "🛍 Shop":

        shop(
            chat_id,
            player
        )

    elif text == "🏆 My Stats":

        stats(
            chat_id,
            player
        )

    elif text == "🏅 Leaderboard":

        leaderboard(
            chat_id
        )

    elif text == "👥 Referral":

        referral(
            chat_id,
            player
        )

    # ========================================================
    # BUSINESSES
    # ========================================================

    elif text == "🍋 Lemonade Stand":

        buy_business(
            chat_id,
            player,
            "lemonade"
        )

    elif text == "🍕 Pizza Shop":

        buy_business(
            chat_id,
            player,
            "pizza"
        )

    elif text == "🛒 Supermarket":

        buy_business(
            chat_id,
            player,
            "market"
        )

    elif text == "🏢 Business Tower":

        buy_business(
            chat_id,
            player,
            "tower"
        )

    elif text == "👑 Mega Empire":

        buy_business(
            chat_id,
            player,
            "empire"
        )

    # ========================================================
    # SHOP
    # ========================================================

    elif text in [

        "⚡ Energy Pack",
        "🔥 2x Coins — 24h",
        "🚀 Mega Boost — 7 Days",
        "🎁 Premium Chest",
        "👑 VIP — 30 Days"

    ]:

        handle_shop_button(
            chat_id,
            text
        )

    # ========================================================
    # BACK
    # ========================================================

    elif text == "🔙 Main Menu":

        send_message(

            chat_id,

            "🏠 MAIN MENU",

            MAIN_KEYBOARD

        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    else:

        send_message(

            chat_id,

            "🤔 I don't recognize that.\n\n"
            "Please use the buttons below.",

            MAIN_KEYBOARD

        )

    save_players()


# ============================================================
# UPDATE PROCESSOR
# ============================================================

def process_update(
    update
):

    try:

        # ====================================================
        # MESSAGE
        # ====================================================

        if "message" in update:

            message = update[
                "message"
            ]

            chat = message.get(
                "chat",
                {}
            )

            user = message.get(
                "from",
                {}
            )

            chat_id = chat.get(
                "id"
            )

            if not chat_id:

                return

            # Successful payment
            if message.get(
                "successful_payment"
            ):

                handle_successful_payment(

                    chat_id,

                    user,

                    message[
                        "successful_payment"
                    ]

                )

                return

            text = message.get(
                "text",
                ""
            )

            if not text:

                return

            if text.startswith("/"):

                handle_command(

                    chat_id,
                    user,
                    text

                )

            else:

                handle_text(

                    chat_id,
                    user,
                    text

                )

        # ====================================================
        # PRE CHECKOUT
        # ====================================================

        elif "pre_checkout_query" in update:

            handle_pre_checkout(

                update[
                    "pre_checkout_query"
                ]

            )

    except Exception as error:

        print(
            "UPDATE ERROR:",
            error
        )


# ============================================================
# MAIN BOT LOOP
# ============================================================

def run_bot():

    print("")
    print("========================================")
    print("        COIN RUSH BOT STARTED")
    print("========================================")
    print("")

    # --------------------------------------------------------
    # Delete webhook so polling works correctly
    # --------------------------------------------------------

    telegram(
        "deleteWebhook",
        {
            "drop_pending_updates": False
        }
    )

    offset = 0

    while True:

        try:

            response = telegram(

                "getUpdates",

                {
                    "offset": offset,

                    "timeout": 30,

                    "allowed_updates": [

                        "message",
                        "pre_checkout_query"

                    ]
                }

            )

            if not response:

                time.sleep(2)

                continue

            if not response.get(
                "ok"
            ):

                print(
                    "Polling error:",
                    response
                )

                time.sleep(5)

                continue

            updates = response.get(
                "result",
                []
            )

            for update in updates:

                offset = (
                    update["update_id"]
                    + 1
                )

                process_update(
                    update
                )

        except KeyboardInterrupt:

            print(
                "Bot stopped."
            )

            break

        except Exception as error:

            print(
                "MAIN LOOP ERROR:",
                error
            )

            time.sleep(5)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run_bot()
