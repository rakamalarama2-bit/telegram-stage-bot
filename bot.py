import asyncio
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGE_TOPIC_ID = 4

# Track violations
violations = {}


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    # ---------------------------
    # CHECK EARLY DELETE (20 sec)
    # ---------------------------

    await asyncio.sleep(20)

    try:
        await context.bot.forward_message(
            chat_id,
            chat_id,
            message_id
        )
    except BadRequest:

        violations[user_id] = violations.get(user_id, 0) + 1
        strike = violations[user_id]

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            text=f"⚠️ {username} violation point {strike}/3: Media removed under 20 seconds."
        )

        print("Early deletion violation.")

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

    # ---------------------------
    # NORMAL FLOW
    # ---------------------------

    await asyncio.sleep(100)  # remaining time to reach 2 minutes

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text="⏰ Please delete your image/video now."
        )

        print("Reminder sent.")

    except BadRequest:
        print("Media already deleted before reminder.")
        return

    # Wait 1 more minute
    await asyncio.sleep(60)

    try:
        await context.bot.delete_message(chat_id, message_id)
        print("Media auto-deleted.")

    except BadRequest:
        print("User deleted before auto-delete.")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        (filters.PHOTO | filters.VIDEO) & filters.ChatType.SUPERGROUP,
        media_handler
    )
)

print("Bot running...")
app.run_polling()
