import asyncio
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Topic IDs
STAGE_TOPIC_ID = 4
POLICY_TOPIC_ID = 6
HOWTOPLAY_TOPIC_ID = 12
ANNOUNCEMENT_TOPIC_ID = 19

# Strike system memory (resets if bot restarts)
user_strikes = {}

# 🚨 Words that cause permanent ban
banned_words = [
    "atabs", "bata", "teen", "teenager",
    "underage", "child", "children"
]

# ⚠️ Bullying words (3 strikes system)
bully_words = [
    "pangit", "ugly", "stupid",
    "hindi maganda", "di maganda",
    "mataba", "nakakasuka", "fat",
    "ampangit", "not sexy"
]


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    chat_id = message.chat_id
    user = message.from_user
    user_id = user.id
    text = (message.text or "").lower()

    thread_id = message.message_thread_id

    # -----------------------------------
    # 1️⃣ LOCK POLICY & HOW TO PLAY
    # -----------------------------------
    if thread_id in [POLICY_TOPIC_ID, HOWTOPLAY_TOPIC_ID]:
        await message.delete()
        return

    # -----------------------------------
    # 2️⃣ ANNOUNCEMENT ADMIN ONLY
    # -----------------------------------
    if thread_id == ANNOUNCEMENT_TOPIC_ID:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            await message.delete()
        return

    # -----------------------------------
    # 3️⃣ AUTO BAN FOR CHILD WORDS
    # -----------------------------------
    for word in banned_words:
        if word in text:
            await message.delete()
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🚫 User banned for violating child safety policy."
            )
            return

    # -----------------------------------
    # 4️⃣ STRIKE SYSTEM FOR BULLYING
    # -----------------------------------
    for word in bully_words:
        if word in text:
            await message.delete()

            strikes = user_strikes.get(user_id, 0) + 1
            user_strikes[user_id] = strikes

            if strikes < 3:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ Warning {strikes}/3 for {user.first_name}. Please respect others."
                )
            else:
                await context.bot.ban_chat_member(
                    chat_id,
                    user_id,
                    until_date=int(time.time()) + 172800  # 2 days
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⛔ {user.first_name} has been banned for 2 days (3 strikes)."
                )
                user_strikes[user_id] = 0

            return

    # -----------------------------------
    # 5️⃣ STAGE PHOTO REMINDER
    # -----------------------------------
    if message.photo and thread_id == STAGE_TOPIC_ID:
        message_id = message.message_id

        await asyncio.sleep(120)

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=STAGE_TOPIC_ID,
                reply_to_message_id=message_id,
                text="⏰ Please delete your image now."
            )
        except BadRequest:
            pass


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.ALL & filters.ChatType.SUPERGROUP, handle_all_messages))

print("Bot running...")
app.run_polling()
