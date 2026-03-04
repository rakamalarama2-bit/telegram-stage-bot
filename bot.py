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
    user = message.from_user

    # Determine username mention
    if user.username:
        username = f"@{user.username}"
    else:
        username = user.first_name

    print("Photo detected:", message_id)

    # ⏳ WAIT 2 MINUTES BEFORE WARNING
    await asyncio.sleep(120)

    try:
        # Send reminder tagging the user
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text=f"⏰ {username} please delete your image now.\n\n⚠️ If not removed, the bot will delete it in 2 minutes."
        )

        print("Reminder sent.")

    except BadRequest:
        # Photo already deleted
        print("Photo already deleted before reminder.")
        return

    # ⏳ WAIT 2 MORE MINUTES AFTER WARNING
    await asyncio.sleep(120)

    try:
        # Try deleting the original photo
        await context.bot.delete_message(chat_id, message_id)

        # Notify group that it was removed
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            text=f"🗑️ {username}'s image was automatically deleted after the warning."
        )

        print("Photo auto-deleted after warning.")

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
