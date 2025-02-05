import asyncio
import traceback
import json
import time

from logging import getLogger
from threading import Lock, Thread
from pathlib import Path
from time import time as getTime
# from asyncio import create_task as createTask, get_running_loop as getRunningLoop

from telegram import Update, File, Message, error
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
    ContextTypes,
)

from . import bot_replies
from modules.models.issue import Issue
from modules.review_pipeline import ReviewPipeline, ReviewResult, UUID
from modules.upload_review import upload_review
from settings import TELEGRAM_AUDIO_DIR, LOGGER_NAME, ALLOWED_EXTENSIONS
from keys import TELEGRAM_BOT_TOKEN


logger__ = getLogger(LOGGER_NAME)


class TelegramBot:
    def __init__(self, review_pipeline: ReviewPipeline):
        self.__review_pipe = review_pipeline
        self.__result_uuids: dict[UUID, tuple[Path, Message]] = {}
        self.__results_lock = Lock()
        self.__thread = Thread(target=self.__review_result_watcher, daemon=True)

        self.__thread.start()

    def start_telegram_bot(self):
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

        try:
            # Get the audio file
            file = update.message.audio or update.message.voice

            # Check if an audio has been uploaded
            if file is None:
                await update.message.reply_text(
                    bot_replies.ATTACHEMENT_DENIED, reply_to_message_id=update.message.id
                )
                return

            file_info: File = await context.bot.get_file(file.file_id)

            if update.message.audio:
                # If file is an audio file
                file_name = update.message.audio.file_name
            else:
                # If file is a voice message
                file_name = "voice.ogg"

            if file_name is None:
                await update.message.reply_text(
                    bot_replies.ATTACHEMENT_DENIED, reply_to_message_id=update.message.id
                )
                return

            # Check if file extension is supported
            file_ext = file_name[file_name.rfind(".") :]
            if file_ext not in ALLOWED_EXTENSIONS:
                await update.message.reply_text(
                    f"{bot_replies.ATTACHEMENT_DENIED}{file_ext}", reply_to_message_id=update.message.id
                )
                return

            # Reply to the user that his audio has been received
            reply_await = update.message.reply_text(
                bot_replies.REVIEW_ACCEPTED, reply_to_message_id=update.message.id
            )

            # Get sender's username
            if update.message.from_user:
                username = update.message.from_user.username

            # Make username anonymous if no username was found
            if username is None:
                username = "Anonymous"

            # Make the new file name
            new_file_name = f"tg@{username}_{int(getTime())}{file_ext}"

            # Download the file
            file_path = TELEGRAM_AUDIO_DIR / new_file_name
            await file_info.download_to_drive(file_path.absolute().as_posix())

            with self.__results_lock:
                self.__result_uuids[self.__review_pipe.queue_audio(file_path)] = (
                    file_path,
                    update.message,
                )

            await reply_await
        
        except error.TimedOut or error.NetworkError as ex:
            logger__.error(f"Timeout: {ex}:\n{traceback.format_exc()}")
            await update.message.reply_text(bot_replies.RETREIVE_ERROR)

    async def __handle_text(self, update: Update, context: CallbackContext):
        if update.message is None:
            logger__.warning("Update does not contain Message.", stack_info=True)
            return

        if update.message.text is None:
            logger__.warning("Message does not contain any text.", stack_info=True)
            return

        # Reply to the user that his audio has been received
        reply_await = update.message.reply_text(
            bot_replies.REVIEW_ACCEPTED, reply_to_message_id=update.message.id
        )

        # Get sender's username
        if update.message.from_user:
            username = update.message.from_user.username

        # Make username anonymous if no username was found
        if username is None:
            username = "Anonymous"

        with self.__results_lock:
            self.__result_uuids[self.__review_pipe.queue_text(update.message.text)] = (
                Path(f"tg@{username}_{int(getTime())}.txt"),
                update.message,
            )

        await reply_await

        # (_, review_result) = await asyncio.gather(reply_await, result_await)

        # # Transcribe it, and upload it
        # result_await = self.__wait_for_result(self.__review_pipe.queue_text(update.message.text))

        # (_, review_result) = asyncio.gather(reply_await, result_await)

        # await self.__handle_review_result(update.message, review_result)

    def __review_result_watcher(self):
        while True:
            time.sleep(5)

            uuids: list[tuple[UUID, ReviewResult]] = []

            with self.__results_lock:
                for _uuid in self.__result_uuids:
                    review_result = self.__review_pipe.get_result_by_uuid(_uuid)

                    if review_result is not None:
                        uuids.append((_uuid, review_result))

            loop = asyncio.new_event_loop()
            for _uuid, _review_result in uuids:
                loop.run_until_complete(
                    self.__handle_review_result(
                        user_message=self.__result_uuids[_uuid][1],
                        review_result=_review_result,
                        audio_path=self.__result_uuids[_uuid][0],
                    )
                )

                self.__result_uuids.pop(_uuid)

    async def __error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""
        # Log the error before we do anything else, so we can see it even if something breaks.
        logger__.error("Exception while handling an update:", exc_info=context.error)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__ if context.error is not None else None
        )
        tb_string = "".join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"update:\n{(json.dumps(update_str, indent=2, ensure_ascii=False))}\n\n"
            f"context.chat_data:\n{str(context.chat_data)}\n\n"
            f"context.user_data:{str(context.user_data)}\n\n"
            f"{tb_string}"
        )

        logger__.error(message)

        # # Finally, send the message
        # await context.bot.send_message(
        #     chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
        # )

    async def __handle_review_result(
        self,
        user_message: Message,
        review_result: ReviewResult,
        audio_path: Path,
    ):
        if not review_result.completed:
            await user_message.reply_text(
                bot_replies.TRANSCRIPTION_ERROR, reply_to_message_id=user_message.id
            )
            return

        if not upload_review(
            audio_review_path=audio_path,
            text_review=review_result.corrected_text,
            text_summary=review_result.summary,
            issues=review_result.issues,
        ):
            await user_message.reply_text(
                bot_replies.UPLOAD_ERROR, reply_to_message_id=user_message.id
            )
            return

        await user_message.reply_text(
            self.__issues_to_text(review_result.issues), reply_to_message_id=user_message.id
        )

    def __issues_to_text(self, issues: list[Issue]) -> str:
        if len(issues) == 0:
            return bot_replies.TRANSCRIPTION_DONE_NO_ISSUES

        issues_str_list = ""
        for issue in issues:
            issues_str_list += issue.description.strip(" \n") + "\n"

        return f"{bot_replies.TRANSCRIPTION_DONE_WITH_ISSUES}\n{issues_str_list}\n"


def start_tg_bot(pipeline: ReviewPipeline):
    TelegramBot(pipeline).start_telegram_bot()
