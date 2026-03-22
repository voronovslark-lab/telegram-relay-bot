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
    "Напишите ваш вопрос — менеджер Аниса ответит в ближайшее время.\n\n"
    "Hello!\n"
    "Please send your message and our manager Anisa will reply shortly."
)

AUTO_REPLY_TEXT = (
    "Сообщение получено. Менеджер на связи.\n\n"
    "Message received. The manager is reviewing it."
)

FOLLOWUP_TEXT = (
    "Менеджер скоро ответит. Благодарим за терпение.\n\n"
    "The manager will respond soon. Thank you for your patience."
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
    from_user = msg.get("from", {})
    user_id = str(from_user.get("id"))

    # 🔴 ЕСЛИ ПИШЕТ АДМИН → отправляем обратно пользователю
    if user_id == str(ADMIN_ID):
        if "reply_to_message" in msg:
            original = msg["reply_to_message"]

            if "forward_from" in original:
                target_id = original["forward_from"]["id"]
                text = msg.get("text", "")
                send_to_user(target_id, text)

        return "ok"

    # 🟢 ЕСЛИ ПИШЕТ ПОЛЬЗОВАТЕЛЬ → форвардим админу
    message_id = msg["message_id"]
    chat_id = msg["chat"]["id"]

    forward_to_admin(chat_id, message_id)

    # автоответ 1 раз
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
