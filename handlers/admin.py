from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import CommandHandler, filters

from services import ConsoleLog, FirebaseLog


class Admin:
    def __init__(self, firebase_log: FirebaseLog, console_log: ConsoleLog) -> None:
        self.firebase_logs = firebase_log
        self.console_logs = console_log.with_name(__name__)
        self.command_filter = ~filters.ChatType.PRIVATE & filters.COMMAND

    def handlers(self) -> list:
        from commands import Mute, Ban, Kick
        return [
            CommandHandler("kick", Kick(console_log=self.console_logs), filters=~filters.ChatType.PRIVATE & filters.COMMAND),
            CommandHandler("dkick", Kick(console_log=self.console_logs).with_delete(), filters=~filters.ChatType.PRIVATE & filters.COMMAND),
            CommandHandler("skick", Kick(console_log=self.console_logs).with_silent(), filters=~filters.ChatType.PRIVATE & filters.COMMAND),
            CommandHandler("sdkick", Kick(console_log=self.console_logs).with_silent().with_delete(), filters=~filters.ChatType.PRIVATE & filters.COMMAND),

            CommandHandler("ban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs), filters=self.command_filter),
            CommandHandler("dban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_delete(), filters=self.command_filter),
            CommandHandler("sban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_silent(), filters=self.command_filter),
            CommandHandler("sdban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_delete().with_silent(), filters=self.command_filter),
            CommandHandler("tban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer(), filters=self.command_filter),
            CommandHandler("tdban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer().with_delete(), filters=self.command_filter),
            CommandHandler("tsdban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer().with_delete().with_silent(), filters=self.command_filter),
            CommandHandler("unban", Ban(firebase_log=self.firebase_logs, console_log=self.console_logs).with_invert(), filters=self.command_filter),

            CommandHandler("mute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs), filters=self.command_filter),
            CommandHandler("dmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_delete(), filters=self.command_filter),
            CommandHandler("smute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_silent(), filters=self.command_filter),
            CommandHandler("sdmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_delete().with_silent(), filters=self.command_filter),
            CommandHandler("tmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer(), filters=self.command_filter),
            CommandHandler("tdmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer().with_delete(), filters=self.command_filter),
            CommandHandler("tsdmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_timer().with_delete().with_silent(), filters=self.command_filter),
            CommandHandler("unmute", Mute(firebase_log=self.firebase_logs, console_log=self.console_logs).with_invert(), filters=self.command_filter),
        ]

    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if the user that sent the message is an admin in the chat."""
        user_id = update.effective_user.id
        member = await update.effective_chat.get_member(user_id)
        return member.status in ['administrator', 'creator']

