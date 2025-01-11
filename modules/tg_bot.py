import logging
import time

from telegram import Update, File
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

from modules.audio_transcriber import AudioTranscriber
from settings import TELEGRAM_AUDIO_DIR, LOGGER_NAME
from keys import TELEGRAM_BOT_TOKEN


logger = logging.getLogger(LOGGER_NAME)


# Define the bot functionality
async def __start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me an audio message, and I'll store it.")


async def __handle_audio(update: Update, context: CallbackContext):
    if update.message is None:
        return

    # Get the audio file
    file = update.message.audio or update.message.voice

    # Check if an audio has been uploaded
    if file is None:
        await update.message.reply_text("Sorry, I can accept only audio messages.")
        return

    # Start the file download
    file_info_await = context.bot.get_file(file.file_id)

    if update.message.audio:
        # If file is an audio file
        file_name = update.message.audio.file_name
    else:
        # If file is a voice message
        file_name = "voice.ogg"

    if file_name is None:
        await update.message.reply_text("Sorry, I can't process this file.")
        return

    # Check if file extension is supported
    file_ext = file_name[file_name.rfind(".") :]
    if file_ext not in [".wav", ".ogg", ".mp3"]:
        await update.message.reply_text(f"Sorry, file type '{file_ext}' is not supported.")
        return

    # Get sender's username
    if update.message.from_user:
        username = update.message.from_user.username

    # Make username anonymous if no username was found
    if username is None:
        username = "Anonymous"

    # Make the new file name
    new_file_name = f"tg@{username}_{int(time.time())}{file_ext}"

    # Wait for file info to be received
    file_info: File = await file_info_await

    # Reply to the user that his audio has been received
    reply_await = update.message.reply_text("Your audio has been successfuly received.")

    # Download the file
    file_path = TELEGRAM_AUDIO_DIR / new_file_name
    await file_info.download_to_drive(file_path.absolute().as_posix())

    # Transcribe it, and upload it
    AudioTranscriber().queue_audio_transcription(file_path)

    # Wait for the reply to be delivered
    await reply_await


def start_telegram_bot():
    """Starts the Telegram bot in a blocking manner"""

    # Initialize Application instead of Updater
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", __start))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))

    logger.info("Telegram bot has been started.")

    # Start polling the bot
    application.run_polling()
