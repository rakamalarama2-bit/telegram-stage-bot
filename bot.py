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

    # Wait 2 minutes
    await asyncio.sleep(120)

    try:
        # Try replying directly to the photo
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text="⏰ Please delete your image now."
        )
        print("Reminder sent.")

    except BadRequest as e:
        # If photo was deleted, Telegram throws error
        print("Photo was already deleted. No reminder sent.")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.PHOTO & filters.ChatType.SUPERGROUP, photo_handler)
)

print("Bot running...")
app.run_polling()