import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGE_TOPIC_ID = 4


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    # Must be in a topic
    if message.message_thread_id is None:
        return

    # Only run in STAGE topic
    if message.message_thread_id != STAGE_TOPIC_ID:
        return

    # Only detect photos or videos
    if not (message.photo or message.video):
        return

    chat_id = message.chat_id
    message_id = message.message_id
    user = message.from_user

    username = f"@{user.username}" if user.username else user.first_name

    print("Media detected:", message_id)

    # WAIT 2 MINUTES
    await asyncio.sleep(120)

    # ---------------------------------
    # CHECK IF MESSAGE STILL EXISTS
    # ---------------------------------
    try:
        # forward silently to check existence
        test = await context.bot.forward_message(
            chat_id=chat_id,
            from_chat_id=chat_id,
            message_id=message_id,
            disable_notification=True
        )

        # immediately delete the forwarded test message
        await context.bot.delete_message(chat_id, test.message_id)

    except BadRequest:
        print("Media already deleted before reminder.")
        return

    # ---------------------------------
    # SEND WARNING
    # ---------------------------------
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            reply_to_message_id=message_id,
            text=f"⏰ {username} please delete your image or video now.\n\n⚠️ If not removed, the bot will delete it in 2 minutes."
        )

        print("Reminder sent.")

    except BadRequest:
        print("Message disappeared before warning.")
        return

    # WAIT 2 MORE MINUTES
    await asyncio.sleep(120)

    # ---------------------------------
    # AUTO DELETE
    # ---------------------------------
    try:
        await context.bot.delete_message(chat_id, message_id)

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=STAGE_TOPIC_ID,
            text=f"🗑️ {username}'s media was automatically deleted after the warning."
        )

        print("Media auto-deleted.")

    except BadRequest:
        print("User deleted media before auto-delete.")
        pass


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        (filters.PHOTO | filters.VIDEO) & filters.ChatType.SUPERGROUP,
        media_handler
    )
)

print("Reminder Bot running...")
app.run_polling()
