from datetime import datetime, timezone, timedelta
from typing import Self
from enum import Enum
from json import dumps

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from services import FirebaseLog, ConsoleLog
from services.log import FirebaseAction
from .utils import parse_duration
from handlers.error import UserNotRepliedError, MissingDurationError, MissingReasonError

class Additions(Enum):
    DELETE = "DELETE"
    SILENT = "SILENT"
    TIMER= "TIMER"


class Mute:
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
        until_date = None
        reason = None
        if not self.invert:
            try:
                reason = context.args[0]
            except IndexError:
                raise MissingReasonError(f"Не указана причина для мута – необходимо указать причину в одно слово")

        if not self.invert and Additions.TIMER in self.adds:
            try:
                duration = parse_duration(context.args[1])
                until_date = datetime.now(timezone.utc) + timedelta(seconds=duration)
            except IndexError:
                raise MissingDurationError(f"Не указано время для бана")

        # TODO: Нужно давать юзеру не все права, а только те, которые у него были
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.reply_to_message.from_user.id,
                permissions=ChatPermissions.no_permissions() if not self.invert else ChatPermissions.all_permissions(),
                until_date=until_date if not self.invert else None,
            )
        except AttributeError:
            raise UserNotRepliedError("Не указан пользователь — Необходимо ответить на сообщение пользователя.")

        if not self.invert and Additions.DELETE in self.adds:
            await update.message.reply_to_message.delete()

        if not Additions.SILENT in self.adds:
            if not self.invert:
                await context.bot.send_message(update.effective_chat.id,
                                           f"Пользователь @{update.message.reply_to_message.from_user.username} в мьюте 🤫")
            else:
                await context.bot.send_message(update.effective_chat.id,
                                               f"Пользователь @{update.message.reply_to_message.from_user.username} разговаривает! 🥳")

        log = {
            "user_id": update.message.reply_to_message.from_user.id,
            "chat_id": update.effective_chat.id,
            "message": update.message.reply_to_message.text,
            "reason": reason if reason else "Не указано",
        }

        if not self.invert:
            await self.firebase_logs.awrite(FirebaseAction.MUTE, dumps(log))
        else:
            await self.firebase_logs.awrite(FirebaseAction.UNMUTE, dumps(log))


    async def mute_user(self, context: ContextTypes.DEFAULT_TYPE,
                        message: str, chat_id: int, user_id: int, reason_llm: str,
                        duration: str | None = None) -> None:
        if duration:
            duration = parse_duration(duration)
            until_date = datetime.now(timezone.utc) + timedelta(seconds=duration)
        else:
            until_date = None

        await self.firebase_logs.awrite(FirebaseAction.MUTE, dumps({
            "user_id": user_id,
            "chat_id": chat_id,
            "message": message,
            "reason": f"Автоматическая модерация (LLM) -> {reason_llm}",
        }))

        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )
