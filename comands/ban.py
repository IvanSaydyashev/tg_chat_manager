from datetime import datetime, timezone, timedelta
import re
from typing import Self
from enum import Enum
from json import dumps

from telegram import Update
from telegram.ext import ContextTypes

from services import FirebaseLog, ConsoleLog
from services.log import FirebaseAction

from .utils import parse_duration
from handlers.error import MissingDurationError, UserNotRepliedError

class Additions(Enum):
    DELETE = "DELETE"
    SILENT = "SILENT"
    TIMER= "TIMER"


class Ban:
    def __init__(self, firebase_log: FirebaseLog, console_log: ConsoleLog) -> None:
        self.adds: set[Additions] = set()
        self.invert: bool = False
        self.firebase_logs = firebase_log
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

    def with_timer(self) -> Self:
        """Works only in the MUTE case"""
        self.adds.add(Additions.TIMER)
        return self

    def with_invert(self) -> Self:
        """
        Now it is not MUTE, it is UNMUTE
        The Silent and Timer modes are disabled.
        """
        self.invert = not self.invert
        return self

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # TODO: Добавить причину для бана
        try:
            log = {
                "user_id": update.message.reply_to_message.from_user.id,
                "chat_id": update.effective_chat.id,
                "message": update.message.reply_to_message.text,
                "reason": "",
            }
        except AttributeError:
            raise UserNotRepliedError(f"Не указан пользователь — Необходимо ответить на сообщение пользователя")

        if not self.invert:
            await self.firebase_logs.awrite(FirebaseAction.BAN, dumps(log))
        else:
            await self.firebase_logs.awrite(FirebaseAction.UNBAN, dumps(log))

        until_date = None
        if not self.invert and Additions.TIMER in self.adds:
            try:
                duration = parse_duration(context.args[0])
                until_date = datetime.now(timezone.utc) + timedelta(seconds=duration)
            except IndexError:
                raise MissingDurationError(f"Не указано время для бана")

        if self.invert:
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.reply_to_message.from_user.id
            )
        else:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.reply_to_message.from_user.id,
                until_date=until_date,
                revoke_messages=True if Additions.DELETE in self.adds else False
            )

        if Additions.SILENT in self.adds:
            return

        if not self.invert:
            await context.bot.send_message(update.effective_chat.id,
                                       f"Пользователь @{update.message.reply_to_message.from_user.username} забанен!")
        else:
            await context.bot.send_message(update.effective_chat.id,
                                           f"Пользователь @{update.message.reply_to_message.from_user.username} разбанен! 🥳")

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, duration: str = None):
        if duration:
            duration = parse_duration(context.args[0])
            until_date = datetime.now(timezone.utc) + timedelta(seconds=duration)
        else:
            until_date = None

        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.message.reply_to_message.from_user.id,
            until_date=until_date,
            revoke_messages=True
        )
