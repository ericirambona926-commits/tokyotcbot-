import os
import logging
import requests
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

app = Flask(name)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

API = f"https://api.telegram.org/bot{TOKEN}"

def send(chat_id, message, keyboard=None):
data = {"chat_id": chat_id, "text": message}
if keyboard:
data["reply_markup"] = keyboard

try:
    response = requests.post(
        f"{API}/sendMessage",
        json=data,
        timeout=20
    )
    logging.info("Telegram sendMessage: %s", response.text)
    return response.json()
except Exception:
    logging.exception("Telegram send error")
    return None

def menu():
return {
"inline_keyboard": [
[
{"text": "EUR/USD", "callback_data": "EUR/USD"},
{"text": "AUD/CAD", "callback_data": "AUD/CAD"}
]
]
}

@app.route("/", methods=["GET"])
def home():
return "Tokyo Trading Bot is running!", 200

@app.route("/telegram", methods=["POST"])
def telegram():
if request.headers.get(
"X-Telegram-Bot-Api-Secret-Token"
) != SECRET:
logging.error("Webhook secret mismatch")
return "Unauthorized", 403

data = request.get_json(silent=True) or {}

if "message" in data:
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if text == "/start":
        send(
            chat_id,
            "🤖 TOKYO TRADING BOT\n\nHitamo currency pair:",
            menu()
        )

    elif text == "/help":
        send(
            chat_id,
            "Hitamo EUR/USD cyangwa AUD/CAD muri menu."
        )

    elif text == "/signal":
        send(
            chat_id,
            "⏳ Signal system iracyategurwa. "
            "Nta signal nyayo iratangwa."
        )

if "callback_query" in data:
    query = data["callback_query"]
    chat_id = query["message"]["chat"]["id"]
    pair = query["data"]

    requests.post(
        f"{API}/answerCallbackQuery",
        json={"callback_query_id": query["id"]},
        timeout=15
    )

    if pair in ["EUR/USD", "AUD/CAD"]:
        send(
            chat_id,
            f"📊 {pair}\n\n"
            "⏳ Signal system iracyategurwa. "
            "Nta signal nyayo iratangwa."
        )

return jsonify({"ok": True})

def setup_webhook():
if not TOKEN or not SECRET or not RENDER_URL:
logging.error("Missing environment variables")
return

try:
    response = requests.post(
        f"{API}/setWebhook",
        json={
            "url": f"{RENDER_URL}/telegram",
            "secret_token": SECRET
        },
        timeout=20
    )
    logging.info("Webhook setup: %s", response.text)
except Exception:
    logging.exception("Webhook setup failed")

setup_webhook()
