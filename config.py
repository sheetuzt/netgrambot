import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI", "").strip()
DATABASE_NAME = os.getenv("DATABASE_NAME", "netgram").strip()
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://your-frontend.vercel.app").strip()
SHORTENER_API = os.getenv("SHORTENER_API", "").strip()

admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = []
if admin_ids_raw:
    for x in admin_ids_raw.split(","):
        x = x.strip()
        if x:
            try:
                ADMIN_IDS.append(int(x))
            except ValueError:
                pass

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing")

if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is missing or invalid")
