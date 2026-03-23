import os
import requests
import time
import threading
from flask import Flask, request

app = Flask(__name__)

BOT1_TOKEN = os.environ.get("BOT1_TOKEN")
BOT2_TOKEN = os.environ.get("BOT2_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

SEEN_USERS = set()

WELCOME_TEXT = (
    "Здравствуйте!\n"
    "Напишите ваш вопрос — менеджер ответит в ближайшее время."
)

AUTO_REPLY_TEXT = (
    "Сообщение получено. Менеджер на связи."
)

FOLLOWUP_TEXT = (
    "Менеджер скоро ответит. Спасибо за ожидание."
)

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def forward_to_admin(from_chat_id, message_id):
    url = f"https://api.telegram.org/bot{BOT2_TOKEN}/forwardMessage"
    requests.post(url, json={
        "chat_id": ADMIN_ID,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    })

def send_to_user(user_id, text):
    send_message(BOT1_TOKEN, user_id, text)

def delayed_followup(user_id):
    time.sleep(900)
    if user_id in SEEN_USERS:
        send_to_user(user_id, FOLLOWUP_TEXT)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    msg = data["message"]
    message_id = msg["message_id"]
    chat_id = msg["chat"]["id"]

    # 🔥 ПЕРЕСЫЛАЕМ ВСЁ (включая стикеры, фото, файлы)
    forward_to_admin(chat_id, message_id)

    text = msg.get("text", "")
    from_user = msg.get("from", {})

    user_id = str(from_user.get("id"))
    username = from_user.get("username", "no_username")

    # ЕСЛИ ПИШЕТ АДМИН (ответ)
    if user_id == str(ADMIN_ID):
        if "reply_to_message" in msg:
            original = msg["reply_to_message"].get("text", "")
            if "[UID:" in original:
                target_id = original.split("[UID:")[1].split("]")[0]
                send_to_user(target_id, text)
        return "ok"

    # /start
    if text == "/start":
        send_to_user(user_id, WELCOME_TEXT)
        return "ok"

    # текст дополнительно (чтобы UID был)
    if text:
        formatted = f"👤 @{username} [UID:{user_id}]\n{text}"
        send_message(BOT2_TOKEN, ADMIN_ID, formatted)

    # автоответ
    if user_id not in SEEN_USERS:
        SEEN_USERS.add(user_id)
        send_to_user(user_id, AUTO_REPLY_TEXT)

        threading.Thread(
            target=delayed_followup,
            args=(user_id,),
            daemon=True
        ).start()

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
