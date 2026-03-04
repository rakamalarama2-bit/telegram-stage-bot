import asyncio
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGE_TOPIC_ID = 4

# Track user violations
violations = {}


async def process_media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if message.message_thread_id != STAGE_TOPIC_ID:
        return

    if not (message.photo or message.video):
        return

    chat_id = message.chat_id
    message_id = message.message_id
    user = message.from_user
    user_id = user.id

    username = f"@{user.username}" if user.username else user.first_name

    print("Media detected:", message_id)

    # -------------------------
    # 1️⃣ Check early deletion
    # -------------------------

    await asyncio.sleep(20)

    try:
        await context.bot.forward_message(chat_id, chat_id, message_id)

    except BadRequest:

        violations[user_id] = violations.get(user_id, 0) + 1
        strike = violations[user_id]

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            text=f"⚠️ {username} violation point {strike}/3: Media removed under 20 seconds."
        )

        if strike >= 3:

            await context.bot.ban_chat_member(
                chat_id,
                user_id,
                until_date=int(time.time()) + 172800
            )

            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=STAGE_TOPIC_ID,
                text=f"🚫 {username} banned for 2 days (3 violations)."
            )

            violations[user_id] = 0

        return

    # -------------------------
    # 2️⃣ Reminder at 2 minutes
    # -------------------------

    await asyncio.sleep(100)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text="⏰ Please delete your image/video now."
        )

    except BadRequest:
        return

    # -------------------------
    # 3️⃣ Auto delete at 3 mins
    # -------------------------

    await asyncio.sleep(60)

    try:
        await context.bot.delete_message(chat_id, message_id)
        print("Media auto-deleted.")

    except BadRequest:
        print("User deleted before auto-delete.")


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # run each message in its own task (supports multiple users)
    asyncio.create_task(process_media(update, context))


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        (filters.PHOTO | filters.VIDEO) & filters.ChatType.SUPERGROUP,
        media_handler
    )
)

print("Bot running...")
app.run_polling()
