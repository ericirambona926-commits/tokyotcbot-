import os
import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

API = f"https://api.telegram.org/bot{TOKEN}"

logging.basicConfig(level=logging.INFO)


def send_message(chat_id, message):
    requests.post(
        f"{API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message
        },
        timeout=20
    )


@app.route("/", methods=["GET"])
def home():
    return "Tokyo Trading Bot is running!", 200


@app.route("/telegram", methods=["POST"])
def telegram():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return "Unauthorized", 403

    data = request.get_json(silent=True) or {}
    message = data.get("message", {})

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip().lower()

    if not chat_id:
        return jsonify({"ok": True})

    if text == "/start":
        send_message(
            chat_id,
            "Murakaza neza kuri Tokyo Trading Bot! 🤖\n\n"
            "Koresha /help kugira ngo ubone amabwiriza."
        )

    elif text == "/help":
        send_message(
            chat_id,
            "TOKYO TRADING BOT\n\n"
            "/start - Gutangira\n"
            "/help - Amabwiriza\n"
            "/signal - Gusaba signal\n\n"
            "Icyitonderwa: Signals ntiziratangira gukora."
        )

    elif text == "/signal":
        send_message(
            chat_id,
            "⏳ Sisitemu ya signals iracyategurwa. Tegereza."
        )

    else:
        send_message(chat_id, "Koresha /start cyangwa /help.")

    return jsonify({"ok": True})


def register_webhook():
    if TOKEN and WEBHOOK_SECRET and RENDER_URL:
        try:
            response = requests.post(
                f"{API}/setWebhook",
                json={
                    "url": f"{RENDER_URL}/telegram",
                    "secret_token": WEBHOOK_SECRET
                },
                timeout=20
            )
            logging.info(response.text)
        except Exception:
            logging.exception("Webhook registration failed")


register_webhook()
