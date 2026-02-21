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

            # ищем UID внутри строки
            if "[UID:" in original_text:
                target_id = original_text.split("[UID:")[1].split("]")[0]
                send_to_user(target_id, text)

        return "ok"

    # -----------------------------
    # ЕСЛИ ПИШЕТ ПОЛЬЗОВАТЕЛЬ
    # -----------------------------
    formatted = f"👤 @{username} [UID:{user_id}]\n{text}"
    send_to_admin(formatted)

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
