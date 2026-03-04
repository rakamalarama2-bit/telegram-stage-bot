import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGE_TOPIC_ID = 4  # your confirmed topic id


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Must be in a topic
    if message.message_thread_id is None:
        return

    # Must be STAGE topic only
    if message.message_thread_id != STAGE_TOPIC_ID:
        return

    chat_id = message.chat_id
    message_id = message.message_id

    print("Photo detected:", message_id)

    # ⏳ WAIT 2 MINUTES
    await asyncio.sleep(120)

    try:
        # Send reminder
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text="⏰ Please delete your image now."
        )
        print("Reminder sent.")

    except BadRequest:
        # Photo already deleted
        print("Photo already deleted before reminder.")
        return

    # ⏳ WAIT 1 MORE MINUTE
    await asyncio.sleep(60)

    try:
        # Try deleting the original photo
        await context.bot.delete_message(chat_id, message_id)
        print("Photo auto-deleted after reminder.")

    except BadRequest:
        # Photo already deleted by user
        print("User deleted photo before auto-delete.")
        pass


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.PHOTO & filters.ChatType.SUPERGROUP, photo_handler)
)

print("Bot running...")
app.run_polling()
