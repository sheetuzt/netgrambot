import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from cinemagoer import Cinemagoer

from config import BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, FRONTEND_URL
from database import db
from utils import clean_filename, shortify

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

ia = Cinemagoer()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /start triggered")
    await update.message.reply_text(
        "🎬 Welcome to NetGram Bot!\n\n"
        "Commands:\n"
        "/search <movie>\n"
        "/stats\n"
        "/auth\n"
    )

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /search triggered")
    if not context.args:
        await update.message.reply_text("Usage: /search <movie name>")
        return

    query = " ".join(context.args)
    movies = db.search_movies(query)

    if not movies:
        await update.message.reply_text("No movies found! 😔")
        return

    response = "🎬 Search Results:\n\n"
    for movie in movies[:5]:
        response += f"**{movie.get('title', 'Unknown')}**"
        if movie.get("year"):
            response += f" ({movie['year']})"
        response += "\n"
        response += f"⭐ {movie.get('imdbRating', 'N/A')}/10\n"
        response += f"📥 {movie.get('downloadUrl', 'N/A')}\n"
        response += f"🎥 {movie.get('streamUrl', 'N/A')}\n"
        response += f"📱 {movie.get('telegramUrl', 'N/A')}\n\n"

    await update.message.reply_text(response, disable_web_page_preview=True)

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /stats triggered")
    count = db.get_movie_count()
    await update.message.reply_text(f"📊 Total Movies: {count}")

async def auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /auth triggered")
    user = update.effective_user
    if user and user.id in ADMIN_IDS:
        await update.message.reply_text("✅ You are authorized as admin!")
    else:
        await update.message.reply_text("❌ You are not authorized.")

async def private_debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        print(f"📩 Private message received: {update.message.text}")

async def channel_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.channel_post
        if not message:
            return

        doc = message.document
        if not doc:
            return

        file_name = doc.file_name or ""
        lower = file_name.lower()

        if not any(ext in lower for ext in [".mp4", ".mkv", ".avi"]):
            print("⏭ Skipped non-movie file:", file_name)
            return

        metadata = clean_filename(file_name)
        imdb_data = {}

        try:
            if metadata["title"]:
                results = ia.search_movie(metadata["title"])
                if results:
                    movie = ia.get_movie(results[0].movieID)
                    imdb_data = {
                        "imdbRating": movie.get("rating", 0),
                        "genres": [str(g) for g in movie.get("genres", [])],
                        "plot": movie.get("plot outline", ""),
                        "poster": movie.get("cover url", ""),
                    }
        except Exception as e:
            print("IMDb fetch failed:", e)

        chat_id = message.chat.id
        message_id = message.message_id
        telegram_url = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"

        movie_data = {
            "title": metadata["title"],
            "year": metadata["year"],
            "quality": metadata["quality"],
            "language": metadata["language"],
            "file_id": doc.file_id,
            "message_id": message_id,
            "chat_id": chat_id,
            "file_size": doc.file_size,
            "downloadUrl": shortify(telegram_url),
            "streamUrl": shortify(f"{FRONTEND_URL}/stream/{message_id}"),
            "telegramUrl": telegram_url,
            **imdb_data,
        }

        added = db.add_movie(movie_data)
        if added:
            print(f"✅ Added: {metadata['title']} ({metadata['year']})")
        else:
            print(f"ℹ️ Duplicate skipped: {metadata['title']} ({metadata['year']})")

    except Exception as e:
        db.log_error(str(e))
        print("❌ Error processing channel file:", e)

def delete_webhook():
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
            params={"drop_pending_updates": True},
            timeout=20
        )
        print("Webhook delete response:", r.text)
    except Exception as e:
        print("Webhook delete failed:", e)

def main():
    print("🚀 NetGram Bot Starting...")
    delete_webhook()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("search", search_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("auth", auth_handler))

    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, private_debug_handler)
    )

    app.add_handler(
        MessageHandler(filters.Chat(chat_id=CHANNEL_ID) & filters.Document.ALL, channel_file_handler)
    )

    print("✅ Bot is now polling for updates...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
