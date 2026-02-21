import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT1_TOKEN = os.environ.get("BOT1_TOKEN")
BOT2_TOKEN = os.environ.get("BOT2_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

def send_to_admin(text):
    url = f"https://api.telegram.org/bot{BOT2_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_ID, "text": text}
    requests.post(url, data=data)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data:
        user = data["message"]["from"]
        text = data["message"].get("text", "")

        username = user.get("username", "no_username")
        user_id = user.get("id")

        msg = f"👤 @{username} ({user_id}):\n{text}"
        send_to_admin(msg)

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
