from flask import Flask
from threading import Thread
import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, filters, ContextTypes
)

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

BOT_TOKEN = "8574370062:AAFFgBSYoaoURhmgmGlianuRGQ_tiHhzqWU"
YOUR_CHAT_ID = 8537889583
GROUP_ID = -1003902125400

USER_FILE = "users.json"

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f)

user_map = load_users()

async def get_or_create_topic(context, user):
    uid = str(user.id)
    if uid in user_map and "topic_id" in user_map[uid]:
        return user_map[uid]["topic_id"]
    topic = await context.bot.create_forum_topic(
        chat_id=GROUP_ID,
        name=f"{user.full_name}"
    )
    user_map[uid] = {
        "name": user.full_name,
        "username": user.username or "none",
        "topic_id": topic.message_thread_id
    }
    save_users(user_map)
    return topic.message_thread_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == GROUP_ID:
        return
    if update.effective_chat.id == YOUR_CHAT_ID:
        await update.message.reply_text(
            "🤖 Bot is running!\n\n"
            "Each user gets their own topic in your group.\n"
            "Tap any topic and reply to chat with that person!"
        )
        return
    user = update.effective_user
    await get_or_create_topic(context, user)

async def forward_to_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if not msg or not user:
        return

    if update.effective_chat.id == GROUP_ID:
        if msg.message_thread_id and not user.is_bot:
            target_id = None
            for uid, info in user_map.items():
                if info.get("topic_id") == msg.message_thread_id:
                    target_id = int(uid)
                    break
            if target_id and target_id != YOUR_CHAT_ID:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=msg.text
                )
        return

    if update.effective_chat.id == YOUR_CHAT_ID:
        return

    uid = str(user.id)
    topic_id = await get_or_create_topic(context, user)

    await context.bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=topic_id,
        text=f"{msg.text or '[non-text]'}"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, forward_to_me))
app.run_polling()
