import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT1_TOKEN = os.environ.get("BOT1_TOKEN")
BOT2_TOKEN = os.environ.get("BOT2_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
print("DEBUG ADMIN_ID =", ADMIN_ID)
def send_to_admin(text):
    url = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_ID, "text": text}
    requests.post(url, data=data)
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    message = data["message"]
    user = message.get("from")
    text = message.get("text", "")

    user_id = user.get("id")
    username = user.get("username", "no_username")

    # -----------------------------
    # ЕСЛИ ПИШЕТ АДМИН → ЭТО ОТВЕТ
    # -----------------------------
    if str(user_id) == str(ADMIN_ID):

        # проверяем, ответил ли ты на сообщение
        if "reply_to_message" in message:
            original = message["reply_to_message"]["text"]

            # из оригинального сообщения достаём ID пользователя
            if "[UID:" in original:
                target_id = original.split("[UID:")[1].split("]")[0]

                url = f"https://api.telegram.org/bot{BOT1_TOKEN}/sendMessage"
                requests.post(url, json={
                    "chat_id": target_id,
                    "text": text
                })

        return "ok"

    # -----------------------------
    # ЕСЛИ ПИШЕТ ПОЛЬЗОВАТЕЛЬ
    # -----------------------------
    msg = f"👤 @{username} [UID:{user_id}]\n{text}"
    send_to_admin(msg)

    return "ok"
