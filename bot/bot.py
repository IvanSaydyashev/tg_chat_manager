import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, BaseHandler, MessageHandler, filters
from telegram.ext import CommandHandler

from comands import Mute
from services import LLMService, ConsoleLog, FirebaseLog, FirebaseClient
from handlers import Admin
from handlers.error import UserIsAdminError

class Bot:
    def __init__(self, llm_service: LLMService, firebase_client: FirebaseClient, firebase_log: FirebaseLog, console_log: ConsoleLog) -> None:
        self.llm_service = llm_service
        self.firebase_db = firebase_client
        self.firebase_logs = firebase_log
        self.console_logs = console_log.with_name(__name__)
        self.admin = Admin(firebase_log=firebase_log, console_log=console_log)
        self.mute_handler = Mute(firebase_log=firebase_log, console_log=console_log)

    def handlers(self) -> list[BaseHandler]:
        return [
            CommandHandler("help", self.help_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.ChatType.PRIVATE, self.validate),
            *self.admin.handlers(),
        ]

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("Help!")

    async def validate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Validate the message sent by the user."""
        status, reason = await self.llm_service.validate_message(update.message.text)
        msg = update.message
        if 'unsafe' in status:
            user_moderation = await self.firebase_db.read(f"moderation/{msg.chat_id}/{msg.from_user.id}")
            if user_moderation:
                await self.firebase_db.update(f"moderation/{msg.chat_id}/{msg.from_user.id}",
                                        {"strikes": user_moderation['strikes'] + 1})
            else:
                await self.firebase_db.write(f"moderation/{msg.chat_id}/{msg.from_user.id}",
                                       {"strikes": 1})
            user_moderation = await self.firebase_db.read(f"moderation/{msg.chat_id}/{msg.from_user.id}")
            try:
                if user_moderation.get('strikes', 0) >= 3:
                    await context.bot.ban_chat_member(chat_id=msg.chat_id, user_id=msg.from_user.id)
                    await context.bot.send_message(chat_id=msg.from_user.id,
                                                   text=f'Вы были забанены за сообщение: '
                                                        f'{update.message.text}\nПричина: {reason}'
                                                   f'Количество нарушений: {user_moderation["strikes"]}/3')
                else:
                    await self.mute_handler.mute_user(context, msg.chat_id, msg.from_user.id, "1h")
                    await context.bot.send_message(chat_id=msg.from_user.id,
                                                   text=f'Вы были наказаны за сообщение: '
                                                        f'{update.message.text}\nПричина: {reason}'
                                                   f'Количество нарушений: {user_moderation["strikes"]}/3')
            except TelegramError:
                raise UserIsAdminError(f'Не удалось заблокировать пользователя {msg.from_user.username}, т.к. он является администратором чата.')
            await update.message.delete()

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""
        if isinstance(update, Update) and update.message:
            await self.console_logs.awrite(status=logging.ERROR, msg=f'Message "{update.message.text}" caused error: {context.error}')
            if not isinstance(context.error, UserIsAdminError):
                await update.message.reply_text(text=str(context.error))
