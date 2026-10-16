import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fatsecret import Fatsecret

BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = (BASE_DIR / "fatsecret_tokens.json")
load_dotenv(BASE_DIR / ".env", override=True)

CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

if not CONSUMER_KEY or not CONSUMER_SECRET:
    raise ValueError("Check your FatSecret credentials in .env")

with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    tokens = json.load(f)

# Поддерживаем формат, который сохраняет твой fatsecret_auth.py
if "session_token" in tokens:
    session_token = tokens["session_token"]

    if isinstance(session_token, list) and len(session_token) == 2:
        token, token_secret = session_token
    else:
        raise ValueError("Некорректный формат session_token в fatsecret_tokens.json")

else:
    token = tokens.get("oauth_token") or tokens.get("access_token")
    token_secret = (
        tokens.get("oauth_token_secret")
        or tokens.get("access_secret")
        or tokens.get("access_token_secret")
    )

    if not token or not token_secret:
        raise ValueError("Не удалось найти токен и секрет в fatsecret_tokens.json")

fs = Fatsecret(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    session_token=(token, token_secret),
    auth="oauth1",
)

def is_fatsecret_connected():
    print("[DEBUG] Запрашиваю дневник FatSecret")
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        return False
    return True

def get_daily_totals():
    entries = fs.diary.entries_get_v2(date=date.today())

    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbohydrate": 0.0,
    }

    for entry in entries:
        for nutrient in totals:
            totals[nutrient] += float(getattr(entry, nutrient, 0) or 0)

    return totals


if __name__ == "__main__":
    get_daily_totals()
