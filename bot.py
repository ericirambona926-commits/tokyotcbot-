import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Murakaza neza kuri TOKYOTCBOT! 🚀\n"
        "Pocket Option Signals Bot iriteguye.\n"
        "Koresha /help kugira ngo ubone amabwiriza."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "TOKYOTCBOT\n"
        "Tegereza signals zemejwe n'isesengura.\n"
        "BUY / SELL / WAIT"
    )

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

if __name__ == "__main__":
    main()
