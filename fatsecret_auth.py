
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fatsecret import Fatsecret

def auth():
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env", override=True)

    consumer_key = os.getenv("FATSECRET_CONSUMER_KEY")
    consumer_secret = os.getenv("FATSECRET_CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise ValueError("Check Consumer Key and Consumer Secret in .env")

    # Создаём клиент FatSecret
    fs = Fatsecret(consumer_key, consumer_secret)

    # Получаем ссылку для авторизации
    auth_url = fs.get_authorize_url(callback_url="oob")

    print("Открой ссылку в браузере и разреши доступ:")
    print(auth_url)

    pin = input("Введи код подтверждения FatSecret: ").strip()

    if not pin:
        raise ValueError("Код подтверждения не введён")

    # Обмениваем код на токен доступа
    session_token = fs.authenticate(pin)

    # Сохраняем токен локально
    token_path = BASE_DIR / "fatsecret_tokens.json"

    # В разных версиях библиотеки результат может иметь разную структуру
    if isinstance(session_token, dict):
        token_data = session_token
    else:
        token_data = {"session_token": session_token}

    token_path.write_text(
        json.dumps(token_data, indent=2),
        encoding="utf-8",
    )

    print("Авторизация завершена.")
    print(f"Токен сохранён в {token_path}")

if __name__ == "__main__":
    auth()