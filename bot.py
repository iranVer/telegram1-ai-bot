import os
import asyncio
import tempfile
from collections import defaultdict, deque
from threading import Thread

from flask import Flask
from openai import OpenAI

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# حافظه هر کاربر
histories = defaultdict(lambda: deque(maxlen=20))

# حالت فعلی کاربران
user_modes = defaultdict(lambda: "ai")

# =========================================================
# FLASK SERVER FOR RENDER
# =========================================================

web = Flask(__name__)


@web.route("/")
def home():
    return "AI Telegram Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🧠 چت هوش مصنوعی", callback_data="ai"),
            InlineKeyboardButton("📥 دانلودر", callback_data="downloader"),
        ],
        [
            InlineKeyboardButton("🎤 ویس → متن", callback_data="voice"),
            InlineKeyboardButton("🔊 پاسخ صوتی", callback_data="tts"),
        ],
        [
            InlineKeyboardButton("📄 فایل", callback_data="files"),
            InlineKeyboardButton("🧹 پاک کردن حافظه", callback_data="clear"),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def downloader_menu():
    keyboard = [
        [
            InlineKeyboardButton("🎬 دانلود ویدیو", callback_data="download_video"),
        ],
        [
            InlineKeyboardButton("🎵 دانلود صدا", callback_data="download_audio"),
        ],
        [
            InlineKeyboardButton("🔗 ارسال لینک", callback_data="send_link"),
        ],
        [
            InlineKeyboardButton("🔙 منوی اصلی", callback_data="home"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def settings_menu():
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🔙 منوی اصلی", callback_data="home"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_modes[update.effective_user.id] = "ai"

    text = """
🤖 *دستیار هوشمند*

سلام 👋

من یک دستیار هوش مصنوعی چندمنظوره هستم.

🧠 چت با هوش مصنوعی
📥 دانلودر لینک
🎤 تبدیل ویس به متن
🔊 تبدیل متن به صدا
📄 پردازش فایل
🧹 حافظه مکالمه

از منوی زیر انتخاب کن 👇
"""

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# =========================================================
# CALLBACKS
# =========================================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # ---------------- HOME ----------------

    if data == "home":

        user_modes[user_id] = "ai"

        await query.edit_message_text(
            "🤖 *منوی اصلی*\n\n"
            "یکی از گزینه‌های زیر را انتخاب کن:",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

    # ---------------- AI ----------------

    elif data == "ai":

        user_modes[user_id] = "ai"

        await query.edit_message_text(
            "🧠 *حالت هوش مصنوعی فعال شد.*\n\n"
            "پیامت را بفرست و با من صحبت کن.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

    # ---------------- DOWNLOADER ----------------

    elif data == "downloader":

        user_modes[user_id] = "downloader"

        await query.edit_message_text(
            "📥 *دانلودر*\n\n"
            "لینک محتوایی که اجازه دانلودش را داری ارسال کن.",
            parse_mode="Markdown",
            reply_markup=downloader_menu(),
        )

    # ---------------- DOWNLOAD VIDEO ----------------

    elif data == "download_video":

        user_modes[user_id] = "download_video"

        await query.edit_message_text(
            "🎬 لینک ویدیو را ارسال کن.\n\n"
            "⚠️ فقط محتوایی که اجازه دانلودش را داری.",
            reply_markup=downloader_menu(),
        )

    # ---------------- DOWNLOAD AUDIO ----------------

    elif data == "download_audio":

        user_modes[user_id] = "download_audio"

        await query.edit_message_text(
            "🎵 لینک ویدیو را ارسال کن تا صدای آن استخراج شود.",
            reply_markup=downloader_menu(),
        )

    # ---------------- SEND LINK ----------------

    elif data == "send_link":

        user_modes[user_id] = "download_video"

        await query.edit_message_text(
            "🔗 لینک را همینجا بفرست.",
            reply_markup=downloader_menu(),
        )

    # ---------------- VOICE ----------------

    elif data == "voice":

        user_modes[user_id] = "voice"

        await query.edit_message_text(
            "🎤 یک پیام صوتی بفرست.\n\n"
            "من آن را به متن تبدیل می‌کنم.",
            reply_markup=main_menu(),
        )

    # ---------------- TTS ----------------

    elif data == "tts":

        user_modes[user_id] = "tts"

        await query.edit_message_text(
            "🔊 متنی که می‌خواهی به صدا تبدیل شود را بفرست.",
            reply_markup=main_menu(),
        )

    # ---------------- FILES ----------------

    elif data == "files":

        user_modes[user_id] = "files"

        await query.edit_message_text(
            "📄 فایل را ارسال کن.\n\n"
            "فعلاً فایل را دریافت می‌کنم تا بتوانیم قابلیت تحلیل فایل را اضافه کنیم.",
            reply_markup=main_menu(),
        )

    # ---------------- CLEAR ----------------

    elif data == "clear":

        histories[user_id].clear()

        await query.edit_message_text(
            "🧹 حافظه مکالمه پاک شد.",
            reply_markup=main_menu(),
        )

    # ---------------- SETTINGS ----------------

    elif data == "settings":

        await query.edit_message_text(
            "⚙️ تنظیمات",
            reply_markup=settings_menu(),
        )

    # ---------------- LANGUAGE ----------------

    elif data == "lang_fa":

        await query.answer("زبان فارسی انتخاب شد 🇮🇷")

    elif data == "lang_en":

        await query.answer("English selected 🇬🇧")

    # ---------------- HELP ----------------

    elif data == "help":

        await query.edit_message_text(
            """
ℹ️ *راهنما*

🧠 چت:
با هوش مصنوعی صحبت کن.

📥 دانلودر:
لینک محتوایی را که اجازه دانلودش را داری ارسال کن.

🎤 ویس:
پیام صوتی بفرست تا به متن تبدیل شود.

🔊 پاسخ صوتی:
متن بفرست تا به فایل صوتی تبدیل شود.

🧹 پاک کردن حافظه:
حافظه مکالمه پاک می‌شود.
""",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )


# =========================================================
# AI CHAT
# =========================================================

SYSTEM_PROMPT = """
تو یک دستیار هوش مصنوعی حرفه‌ای داخل تلگرام هستی.

ویژگی‌های تو:
- فارسی را روان و طبیعی صحبت کن.
- اگر کاربر انگلیسی صحبت کرد، انگلیسی جواب بده.
- دوستانه و مفید باش.
- پاسخ‌ها را واضح و مرتب بنویس.
- در مسائل آموزشی مرحله‌به‌مرحله توضیح بده.
- اگر اطلاعات کافی نداری، صادقانه بگو.
- اطلاعات ساختگی ارائه نکن.
"""


async def ai_chat(update: Update, text: str):

    user_id = update.effective_user.id

    histories[user_id].append({
        "role": "user",
        "content": text,
    })

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    messages.extend(list(histories[user_id]))

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "نتونستم پاسخ مناسبی تولید کنم."

        histories[user_id].append({
            "role": "assistant",
            "content": answer,
        })

        return answer

    except Exception as e:

        print("AI ERROR:", repr(e))

        return "❌ ارتباط با هوش مصنوعی با مشکل مواجه شد."


# =========================================================
# DOWNLOAD
# =========================================================

def download_media(url, audio=False):

    import yt_dlp

    temp_dir = tempfile.mkdtemp()

    if audio:

        output = os.path.join(
            temp_dir,
            "%(title)s.%(ext)s"
        )

        options = {
            "format": "bestaudio/best",
            "outtmpl": output,
            "noplaylist": True,
            "quiet": True,
        }

    else:

        output = os.path.join(
            temp_dir,
            "%(title)s.%(ext)s"
        )

        options = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output,
            "noplaylist": True,
            "quiet": True,
        }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)

        return filename


async def handle_download(update: Update, url: str, audio=False):

    message = await update.message.reply_text(
        "⏳ در حال پردازش لینک..."
    )

    try:

        filename = await asyncio.to_thread(
            download_media,
            url,
            audio
        )

        if not os.path.exists(filename):

            await message.edit_text(
                "❌ فایل دانلود نشد."
            )

            return

        await message.edit_text(
            "📤 فایل آماده شد، در حال ارسال..."
        )

        with open(filename, "rb") as file:

            if audio:

                await update.message.reply_audio(
                    audio=file
                )

            else:

                await update.message.reply_document(
                    document=file
                )

        try:
            os.remove(filename)
        except:
            pass

    except Exception as e:

        print("DOWNLOAD ERROR:", repr(e))

        await message.edit_text(
            "❌ نتونستم این لینک رو پردازش کنم.\n\n"
            "ممکنه لینک خصوصی، نامعتبر یا توسط سرویس مقصد قابل دریافت نباشه."
        )


# =========================================================
# VOICE
# =========================================================

async def handle_voice(update: Update):

    message = await update.message.reply_text(
        "🎤 در حال تبدیل ویس به متن..."
    )

    temp_file = None

    try:

        voice = update.message.voice

        file = await context_bot_file(update, voice.file_id)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".ogg",
            delete=False
        )

        temp_file.close()

        await file.download_to_drive(temp_file.name)

        with open(temp_file.name, "rb") as audio:

            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
            )

        text = transcription.text

        await message.edit_text(
            "📝 متن ویس:\n\n" + text
        )

    except Exception as e:

        print("VOICE ERROR:", repr(e))

        await message.edit_text(
            "❌ تبدیل ویس انجام نشد."
        )

    finally:

        if temp_file:

            try:
                os.remove(temp_file.name)
            except:
                pass


async def context_bot_file(update, file_id):

    return await update.get_bot().get_file(file_id)


# =========================================================
# TEXT TO SPEECH
# =========================================================

async def handle_tts(update: Update, text: str):

    message = await update.message.reply_text(
        "🔊 در حال ساخت فایل صوتی..."
    )

    temp = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )

    temp.close()

    try:

        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=text,
        ) as response:

            response.stream_to_file(temp.name)

        with open(temp.name, "rb") as audio:

            await update.message.reply_audio(
                audio=audio,
                title="AI Voice",
            )

        await message.delete()

    except Exception as e:

        print("TTS ERROR:", repr(e))

        await message.edit_text(
            "❌ ساخت صدا انجام نشد."
        )

    finally:

        try:
            os.remove(temp.name)
        except:
            pass


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    mode = user_modes[user_id]

    # ---------------- DOWNLOAD ----------------

    if mode in ["download_video", "download_audio"]:

        if not text.startswith(("http://", "https://")):

            await update.message.reply_text(
                "🔗 لطفاً یک لینک معتبر ارسال کن."
            )

            return

        await handle_download(
            update,
            text,
            audio=(mode == "download_audio")
        )

        return

    # ---------------- TTS ----------------

    if mode == "tts":

        await handle_tts(update, text)

        return

    # ---------------- AI ----------------

    await update.message.chat.send_action("typing")

    answer = await ai_chat(
        update,
        text
    )

    await update.message.reply_text(
        answer
    )


# =========================================================
# VOICE HANDLER
# =========================================================

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await handle_voice(update)


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# =========================================================
# MAIN
# =========================================================

def main():

    Thread(
        target=run_web,
        daemon=True
    ).start()

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "clear",
            clear
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("🤖 BOT STARTED")

    application.run_polling()


if __name__ == "__main__":
    main()
