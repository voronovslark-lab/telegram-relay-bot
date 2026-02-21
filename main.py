import os
import requests
import time
import threading
from flask import Flask, request

app = Flask(__name__)

BOT1_TOKEN = os.environ.get("BOT1_TOKEN")
BOT2_TOKEN = os.environ.get("BOT2_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

print("DEBUG ADMIN_ID =", ADMIN_ID)

# -----------------------------
# ТЕКСТЫ СООБЩЕНИЙ (RU + EN)
# -----------------------------

WELCOME_TEXT = """Сообщение получено.
Менеджер на связи и ответит в ближайшее время. Спасибо за ожидание.

Message received.
The manager will reply as soon as possible. Thank you for waiting."""

FIRST_FOLLOWUP = """Спасибо за ожидание.
Менеджер скоро ответит.

Thank you for your patience.
The manager will reply shortly."""

SECOND_FOLLOWUP = """Сейчас нерабочее время.
Менеджер ответит, как только будет на связи.

It is currently outside business hours.
The manager will respond as soon as possible."""

# -----------------------------
# ХРАНИМ АКТИВНЫЕ ДИАЛОГИ
# -----------------------------

ACTIVE_CHATS = {}
SEEN_USERS = set()

FIRST_DELAY = 20 * 60      # 20 минут
SECOND_DELAY = 2 * 60 * 60 # 2 часа

# -----------------------------
# ОТПРАВКА СООБЩЕНИЙ
# -----------------------------

def send_to_admin(text):
    url = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": ADMIN_ID,
        "text": text
    })

def send_to_user(user_id, text):
    url = f"https://api.telegram.org/bot{BOT1_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": user_id,
        "text": text
    })

# -----------------------------
# FOLLOW-UP ТАЙМЕР
# -----------------------------

def followup_worker(user_id):
    time.sleep(FIRST_DELAY)

    if user_id in ACTIVE_CHATS:
        send_to_user(user_id, FIRST_FOLLOWUP)

    time.sleep(SECOND_DELAY - FIRST_DELAY)

    if user_id in ACTIVE_CHATS:
        send_to_user(user_id, SECOND_FOLLOWUP)

# -----------------------------
# WEBHOOK
# -----------------------------

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    msg = data["message"]
    from_user = msg.get("from", {})
    text = msg.get("text", "")

    user_id = str(from_user.get("id"))
    username = from_user.get("username", "no_username")

    # -----------------------------
    # ЕСЛИ ПИШЕТ АДМИН — ЭТО ОТВЕТ
    # -----------------------------
    if user_id == str(ADMIN_ID):

        if "reply_to_message" in msg:
            original_text = msg["reply_to_message"].get("text", "")

            if "[UID:" in original_text:
                target_id = original_text.split("[UID:")[1].split("]")[0]

                send_to_user(target_id, text)

                # закрываем ожидание
                if target_id in ACTIVE_CHATS:
                    del ACTIVE_CHATS[target_id]

        return "ok"

    # -----------------------------
    # ЕСЛИ ПИШЕТ ПОЛЬЗОВАТЕЛЬ
    # -----------------------------
    formatted = f"👤 @{username} [UID:{user_id}]\n{text}"
    send_to_admin(formatted)

    # автоответ только один раз
    if user_id not in SEEN_USERS:
        send_to_user(user_id, WELCOME_TEXT)
        SEEN_USERS.add(user_id)

    # запускаем таймер ожидания
    if user_id not in ACTIVE_CHATS:
        ACTIVE_CHATS[user_id] = time.time()
        threading.Thread(target=followup_worker, args=(user_id,), daemon=True).start()

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

if name == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
