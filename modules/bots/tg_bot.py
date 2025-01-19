import asyncio
import traceback
import json

# from multiprocessing import SimpleQueue
from pathlib import Path
from logging import getLogger
from time import time as getTime

from telegram import Update, File, Message
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
    ContextTypes,
)

from . import bot_replies
from modules.reviewing.review_context import ReviewQueues
from modules.reviewing.bot_strategy import BotReviewStrategy, UserDialog
from settings import TELEGRAM_AUDIO_DIR, LOGGER_NAME
from keys import TELEGRAM_BOT_TOKEN


logger__ = getLogger(LOGGER_NAME)


class TelegramUserDialog(UserDialog):
    def __init__(self, event_loop: asyncio.AbstractEventLoop, message: Message) -> None:
        self.event_loop = event_loop
        self.__message = message

    def send_message(self, message: str) -> None:
        self.__async_to_sync(
            self.__message.reply_text(message, reply_to_message_id=self.__message.id)
        )

    def send_image(self, image_path: Path) -> None:
        with open(image_path, "rb") as image:
            self.__async_to_sync(self.__message.reply_photo(image, caption=bot_replies.START_REPLY))

    def __async_to_sync(self, awaitable_target):
        # loop = asyncio.new_event_loop()
        # self.event_loop.create_task(awaitable_target()).add_done_callback(lambda t: print("Done"))
        # loop.close()
        return asyncio.run_coroutine_threadsafe(awaitable_target, self.event_loop).result()


class TelegramBot:
    def __init__(self, review_queues: ReviewQueues) -> None:
        self.__review_queues = review_queues

    def run_telegram_bot(self):
        """Starts the Telegram bot in a blocking manner"""

        # Initialize Application instead of Updater
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.__start))
        # application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))
        application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.__handle_audio))
        application.add_handler(MessageHandler(filters.TEXT, self.__handle_text))

        application.add_error_handler(self.__error_handler)

        logger__.info("Telegram bot has been started.")

        # Start polling the bot
        application.run_polling()

    async def __start(self, update: Update, context: CallbackContext):
        if update.message is None:
            logger__.warning("Update does not contain Message", stack_info=True)
            return

        with open(bot_replies.START_ATTACHEMENT_PATH, "rb") as image:
            await update.message.reply_photo(image, caption=bot_replies.START_REPLY)

    async def __handle_audio(self, update: Update, context: CallbackContext):
        if update.message is None:
            logger__.warning("Update does not contain Message", stack_info=True)
            return

        # Get the audio file
        file = update.message.audio or update.message.voice

        # Check if an audio has been uploaded
        if file is None:
            await update.message.reply_text(bot_replies.ATTACHEMENT_DENIED)
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
            await update.message.reply_text(bot_replies.ATTACHEMENT_DENIED)
            return

        # Check if file extension is supported
        file_ext = file_name[file_name.rfind(".") :]
        if file_ext not in [".wav", ".ogg", ".mp3"]:
            await update.message.reply_text(f"{bot_replies.ATTACHEMENT_DENIED}{file_ext}")
            return

        # Get sender's username
        if update.message.from_user:
            username = update.message.from_user.username

        # Make username anonymous if no username was found
        if username is None:
            username = "Anonymous"

        # Make the new file name
        new_file_name = f"tg@{username}_{int(getTime())}{file_ext}"

        # Wait for file info to be received
        file_info: File = await file_info_await

        # Reply to the user that his audio has been received
        reply_await = update.message.reply_text(bot_replies.REVIEW_ACCEPTED)

        # Download the file
        file_path = TELEGRAM_AUDIO_DIR / new_file_name
        await file_info.download_to_drive(file_path.absolute().as_posix())

        # Transcribe it, and upload it
        self.__review_queues.audio_queue.put(
            (
                BotReviewStrategy(TelegramUserDialog(asyncio.get_running_loop(), update.message)),
                file_path,
            )
        )

        # Wait for the reply to be delivered
        await reply_await

    async def __handle_text(self, update: Update, context: CallbackContext):
        if update.message is None:
            logger__.warning("Update does not contain Message.", stack_info=True)
            return

        if update.message.text is None:
            logger__.warning("Message does not contain any text.", stack_info=True)
            return

        # Reply to the user that his audio has been received
        reply_await = update.message.reply_text(bot_replies.REVIEW_ACCEPTED)

        # Transcribe it, and upload it
        self.__review_queues.text_queue.put(
            (
                BotReviewStrategy(TelegramUserDialog(asyncio.get_running_loop(), update.message)),
                update.message.text,
            )
        )

        await reply_await

    async def __error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger__.error("Exception while handling an update:", exc_info=context.error)

        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__ if context.error is not None else None
        )
        tb_string = "".join(tb_list)

        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"update:\n{(json.dumps(update_str, indent=2, ensure_ascii=False))}\n\n"
            f"context.chat_data:\n{str(context.chat_data)}\n\n"
            f"context.user_data:{str(context.user_data)}\n\n"
            f"{tb_string}"
        )

        logger__.error(message)
