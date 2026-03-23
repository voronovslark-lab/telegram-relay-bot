import os
import requests
import time
import threading
from flask import Flask, request

app = Flask(__name__)

BOT1_TOKEN = os.environ.get("BOT1_TOKEN")  # клиент
BOT2_TOKEN = os.environ.get("BOT2_TOKEN")  # админ
ADMIN_ID = str(os.environ.get("ADMIN_ID"))

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

# 🔥 отправка текста
def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# 🔥 копирование ЛЮБОГО сообщения (стикеры, фото и т.д.)
def copy_message(token, chat_id, from_chat_id, message_id):
    url = f"https://api.telegram.org/bot{token}/copyMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    })

# 🔥 пользователь → админ
def forward_to_admin(from_chat_id, message_id):
    url = f"https://api.telegram.org/bot{BOT2_TOKEN}/forwardMessage"
    requests.post(url, json={
        "chat_id": ADMIN_ID,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    })

def delayed_followup(user_id):
    time.sleep(900)
    if user_id in SEEN_USERS:
        send_message(BOT1_TOKEN, user_id, FOLLOWUP_TEXT)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    msg = data.get("message")

    if not msg:
        return "ok"

    chat_id = str(msg["chat"]["id"])
    user_id = str(msg.get("from", {}).get("id"))
    text = msg.get("text", "")

    # 🔴 ЕСЛИ ПИШЕТ АДМИН
    if user_id == ADMIN_ID:

        if "reply_to_message" in msg:
            original = msg["reply_to_message"]

            if "forward_from" in original:
                target_id = str(original["forward_from"]["id"])

                # 🔥 отправляем ЛЮБОЙ тип (стикер, фото и т.д.)
                copy_message(BOT1_TOKEN, target_id, chat_id, msg["message_id"])

        return "ok"

    # 🟢 ЕСЛИ ПИШЕТ ПОЛЬЗОВАТЕЛЬ

    # пересылаем админу ВСЁ
    forward_to_admin(chat_id, msg["message_id"])

    # /start
    if text == "/start":
        send_message(BOT1_TOKEN, user_id, WELCOME_TEXT)
        return "ok"

    # автоответ 1 раз
    if user_id not in SEEN_USERS:
        SEEN_USERS.add(user_id)

        send_message(BOT1_TOKEN, user_id, AUTO_REPLY_TEXT)

        threading.Thread(
            target=delayed_followup,
            args=(user_id,),
            daemon=True
        ).start()

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
