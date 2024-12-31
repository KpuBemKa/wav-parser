import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

from modules.audio_transcriber import AudioTranscriber
from settings import TELEGRAM_AUDIO_DIR, LOGGER_NAME
from keys import TELEGRAM_BOT_TOKEN


logger = logging.getLogger(LOGGER_NAME)


# Define the bot functionality
async def __start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me an audio message, and I'll store it as a file.")


async def __handle_audio(update: Update, context: CallbackContext):
    if update.message is None:
        return

    # Get the audio file
    file = update.message.audio or update.message.voice

    if file is None:
        await update.message.reply_text("I can accept only audio messages.")
        return

    file_id = file.file_id
    file_info = await context.bot.get_file(file_id)
    file_name = f"{file_id}.ogg"  # Use .ogg for voice messages, modify as needed

    reply_result = update.message.reply_text("Your audio has been successfuly received.")

    # Download the file
    file_path = TELEGRAM_AUDIO_DIR / file_name
    await file_info.download_to_drive(file_path.absolute().as_posix())

    AudioTranscriber().queue_audio_transcription(file_path)

    await reply_result


# Start the Telegram bot in a separate thread
def start_telegram_bot():
    # Initialize Application instead of Updater
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", __start))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))

    logger.info("Telegram bot has been started.")

    # Start polling the bot
    application.run_polling()
