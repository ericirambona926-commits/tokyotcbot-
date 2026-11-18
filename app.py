
import os
import logging
import requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
OTC_KEY = os.environ.get("OTCHARTS_API_KEY")

TG = f"https://api.telegram.org/bot{TOKEN}"
OTC_API = "https://otcharts.com/v1/candles"

PAIRS = [
    "EURUSD_otc",
    "GBPUSD_otc",
    "USDJPY_otc",
    "AUDUSD_otc",
    "BTCUSD_otc"
]

# ---------------------------
# TELEGRAM
# ---------------------------

def tg(method, data=None):
    r = requests.post(
        f"{TG}/{method}",
        json=data or {},
        timeout=20
    )
    r.raise_for_status()
    result = r.json()

    if not result.get("ok"):
        raise Exception(result)

    return result


def send(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    tg("sendMessage", data)


def menu_keyboard():
    return {
        "keyboard": [
            [{"text": "/start"}, {"text": "/help"}],
            [{"text": "/signal"}]
        ],
        "resize_keyboard": True
    }


def pair_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "EUR/USD OTC", "callback_data": "EURUSD_otc"},
                {"text": "GBP/USD OTC", "callback_data": "GBPUSD_otc"}
            ],
            [
                {"text": "USD/JPY OTC", "callback_data": "USDJPY_otc"},
                {"text": "AUD/USD OTC", "callback_data": "AUDUSD_otc"}
            ],
            [
                {"text": "BTC/USD OTC", "callback_data": "BTCUSD_otc"}
            ]
        ]
    }


# ---------------------------
# MARKET DATA
# ---------------------------

def get_candles(symbol):
    if not OTC_KEY:
        raise Exception("OTCHARTS_API_KEY ntabwo yashyizweho.")

    r = requests.get(
        OTC_API,
        headers={
            "Authorization": f"Bearer {OTC_KEY}",
            "User-Agent": "TokyoTradingBot/1.0"
        },
        params={
            "venue": "otc",
            "symbol": symbol,
            "tf": 60,
            "limit": 200
        },
        timeout=25
    )

    if r.status_code != 200:
        raise Exception(f"OTCharts API error: {r.status_code} {r.text[:300]}")

    data = r.json()
    candles = data.get("candles", [])

    if len(candles) < 50:
        raise Exception("Candle data idahagije.")

    return candles


# ---------------------------
# INDICATORS
# ---------------------------

def ema(values, period):
    if len(values) < period:
        return None

    alpha = 2 / (period + 1)

    result = sum(values[:period]) / period

    for value in values[period:]:
        result = alpha * value + (1 - alpha) * result

    return result


def rsi(values, period=14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def macd(values):
    if len(values) < 35:
        return None

    fast = ema(values, 12)
    slow = ema(values, 26)

    if fast is None or slow is None:
        return None

    return fast - slow


# ---------------------------
# ANALYSIS
# ---------------------------

def analyze(candles):
    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    last = closes[-1]

    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    ema50 = ema(closes, 50)

    rsi14 = rsi(closes, 14)
    macd_value = macd(closes)

    momentum = closes[-1] - closes[-5]

    # Candle body and range
    candle_range = highs[-1] - lows[-1]
    body = closes[-1] - float(candles[-1]["open"])

    if candle_range == 0:
        candle_strength = 0
    else:
        candle_strength = abs(body) / candle_range

    bullish = 0
    bearish = 0

    # EMA trend
    if ema9 > ema21:
        bullish += 1
    elif ema9 < ema21:
        bearish += 1

    if last > ema50:
        bullish += 1
    elif last < ema50:
        bearish += 1

    # RSI
    if 50 < rsi14 < 70:
        bullish += 1
    elif 30 < rsi14 < 50:
        bearish += 1

    # MACD
    if macd_value > 0:
        bullish += 1
    elif macd_value < 0:
        bearish += 1

    # Momentum
    if momentum > 0:
        bullish += 1
    elif momentum < 0:
        bearish += 1

    if bullish >= 4 and bullish > bearish:
        direction = "BUY"
        score = bullish

    elif bearish >= 4 and bearish > bullish:
        direction = "SELL"
        score = bearish

    else:
        direction = "NONE"
        score = max(bullish, bearish)

    return {
        "direction": direction,
        "score": score,
        "bullish": bullish,
        "bearish": bearish,
        "rsi": rsi14,
        "ema9": ema9,
        "ema21": ema21,
        "ema50": ema50,
        "macd": macd_value,
        "momentum": momentum,
        "candle_strength": candle_strength,
        "price": last
    }


# ---------------------------
# SIGNAL
# ---------------------------

def make_signal(chat_id, symbol):
    try:
        candles = get_candles(symbol)
        result = analyze(candles)

        if result["direction"] == "NONE":
            send(
                chat_id,
                "⚠️ NTA SIGNAL\n\n"
                f"Asset: {symbol}\n"
                f"RSI: {result['rsi']:.2f}\n"
                f"Bullish votes: {result['bullish']}/5\n"
                f"Bearish votes: {result['bearish']}/5\n\n"
                "Conditions ntizihagije.\n"
                "Tegereza indi setup."
            )
            return

        direction = result["direction"]

        text = (
            "TOKYO OTC SIGNAL\n\n"
            f"Asset: {symbol}\n"
            f"Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
            "Expiry: 1 minute\n\n"
            "ANALYSIS\n"
            f"RSI: {result['rsi']:.2f}\n"
            f"Bullish: {result['bullish']}/5\n"
            f"Bearish: {result['bearish']}/5\n"
            f"EMA trend: {'Bullish' if result['ema9'] > result['ema21'] else 'Bearish'}\n"
            f"Momentum: {'Positive' if result['momentum'] > 0 else 'Negative'}\n\n"
            "⚠️ Score ntabwo ari win-rate.\n"
            "Accuracy ya strategy ntiramenyekana."
        )

        send(chat_id, text)

    except Exception as e:
        logging.exception("Signal error")

        send(
            chat_id,
            "❌ Signal yanze kuboneka.\n\n"
            f"Impamvu: {str(e)[:250]}"
        )


# ---------------------------
# TELEGRAM COMMANDS
# ---------------------------

def process_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    command = text.split()[0].split("@")[0].lower()

    if command == "/start":
        send(
            chat_id,
            "Murakaza neza kuri Tokyo OTC Signal Bot! 🤖\n\n"
            "Bot isesengura OTC candles.\n\n"
            "Koresha /signal kugira ngo uhitemo asset.",
            menu_keyboard()
        )

    elif command == "/help":
        send(
            chat_id,
            "TOKYO OTC BOT\n\n"
            "/start - Gutangira\n"
            "/help - Amabwiriza\n"
            "/signal - Gusaba signal\n\n"
            "Signals zishingiye ku indicators.\n"
            "Nta accuracy ya 80% yemejwe.\n"
            "Signal ishobora gutsindwa.",
            menu_keyboard()
        )

    elif command == "/signal":
        send(
            chat_id,
            "Hitamo OTC asset:",
            pair_keyboard()
        )


# ---------------------------
# WEBHOOK
# ---------------------------

@app.route("/", methods=["GET"])
def home():
    return "Tokyo OTC Bot is running!", 200


@app.route("/telegram", methods=["POST"])
def webhook():

    if SECRET:
        received = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token", ""
        )

        if received != SECRET:
            return "Unauthorized", 401

    update = request.get_json(silent=True) or {}

    if "message" in update:
        process_message(update["message"])

    elif "callback_query" in update:
        callback = update["callback_query"]

        tg("answerCallbackQuery", {
            "callback_query_id": callback["id"]
        })

        symbol = callback.get("data")
        chat_id = callback.get("message", {}).get("chat", {}).get("id")

        if symbol in PAIRS and chat_id:
            make_signal(chat_id, symbol)

    return "OK", 200


# ---------------------------
# INITIAL SETUP
# ---------------------------

def setup():
    commands = [
        {"command": "start", "description": "Gutangira"},
        {"command": "help", "description": "Amabwiriza"},
        {"command": "signal", "description": "Gusaba signal"}
    ]

    tg("setMyCommands", {"commands": commands})

    tg("setChatMenuButton", {
        "menu_button": {
            "type": "commands"
        }
    })

    if RENDER_URL:
        data = {
            "url": f"{RENDER_URL}/telegram"
        }

        if SECRET:
            data["secret_token"] = SECRET

        tg("setWebhook", data)


if TOKEN:
    try:
        setup()
        logging.info("Telegram setup completed.")
    except Exception:
        logging.exception("Setup failed")


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
