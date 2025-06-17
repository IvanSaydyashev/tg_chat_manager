from enum import Enum
from typing import Self

from telegram import Update
from telegram.ext import ContextTypes

from services import ConsoleLog, FirebaseClient
from .utils import is_admin
from handlers.error import UserIsAdminError, UserNotRepliedError


class Additions(Enum):
    GET = "GET"
    RESET = "RESET"

class Strike:
    def __init__(self, console_log: ConsoleLog, firebase_db: FirebaseClient) -> None:
        self.console_logs = console_log.with_name(__name__)
        self.firebase_db = firebase_db
        self.adds: set[Additions] = set()

    def get(self) -> Self:
        """
        Get the current state of the strike counter.
        """
        self.adds.add(Additions.GET)
        return self

    def reset(self) -> Self:
        """
        Reset the strike counter.
        """
        self.adds.add(Additions.RESET)
        return self

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_admin(update):
            raise UserIsAdminError("Команда доступна только администраторам.")

        try:
            msg = update.message
            user = update.message.reply_to_message.from_user
        except AttributeError:
            raise UserNotRepliedError("Не указан пользователь — Необходимо ответить на сообщение пользователя")
        print(user.id)
        if Additions.GET in self.adds:
            strike_count = await self.firebase_db.read(f"moderation/{msg.chat_id}/{user.id}/strikes")
            await context.bot.send_message(msg.chat_id, f"Предупреждений пользователя {user.full_name} сейчас: {strike_count}")
        elif Additions.RESET in self.adds:
            await self.firebase_db.update(f"moderation/{msg.chat_id}/{user.id}", {"strikes": 0})
            await context.bot.send_message(msg.chat_id, f"Предупреждения пользователя {user.full_name} сброшены")
