import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram AI Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "من ربات هوش مصنوعی تو هستم 🤖\n\n"
        "پیامت رو بفرست."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text

        response = client.responses.create(
            model="gpt-5-mini",
            input=text
        )

        await update.message.reply_text(response.output_text)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "متأسفانه مشکلی پیش اومد 😕"
        )


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def main():
    Thread(target=run_web, daemon=True).start()

    bot = Application.builder().token(TELEGRAM_TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("Bot is running...")
    bot.run_polling()


if __name__ == "__main__":
    main()
