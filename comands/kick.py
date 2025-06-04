from typing import Self
from enum import Enum
from telegram import Update
from telegram.ext import ContextTypes

from services import ConsoleLog
from handlers.error import UserNotRepliedError


class Additions(Enum):
    DELETE = "DELETE"
    SILENT = "SILENT"


class Kick:
    def __init__(self, console_log: ConsoleLog) -> None:
        self.adds: set[Additions] = set()
        self.console_logs = console_log.with_name(__name__)

    def with_delete(self) -> Self:
        """
        Works only in the MUTE case
        The message you replied to will be deleted.
        """
        self.adds.add(Additions.DELETE)
        return self

    def with_silent(self) -> Self:
        """
        Works only in the MUTE case
        After the user is banned, the bot will send a notification.
        """
        self.adds.add(Additions.SILENT)
        return self

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.reply_to_message.from_user.id,
                revoke_messages=True if Additions.DELETE in self.adds else False
            )
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.reply_to_message.from_user.id,
            )
        except AttributeError:
            raise UserNotRepliedError("Не указан пользователь — Необходимо ответить на сообщение пользователя.")

        if Additions.SILENT in self.adds:
            return

        await context.bot.send_message(update.effective_chat.id,
                                       f"Пользователь @{update.message.reply_to_message.from_user.username} Кикнут.")
