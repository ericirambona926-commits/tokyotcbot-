
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")

API = f"https://api.telegram.org/bot{TOKEN}"

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = keyboard
    requests.post(f"{API}/sendMessage", json=data, timeout=15)

def main_menu():
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
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        return "Unauthorized", 403

    data = request.get_json(silent=True) or {}

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            send(chat_id, "TOKYO TRADING BOT 🤖\nHitamo currency pair:", main_menu())

        elif text == "/help":
            send(chat_id, "Hitamo EUR/USD cyangwa AUD/CAD muri menu.")

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
                "⏳ Signal system iracyategurwa.\n"
                "Ntukagure cyangwa ngo ugurishe wishingikirije kuri iyi butumwa."
            )

    return jsonify({"ok": True})
