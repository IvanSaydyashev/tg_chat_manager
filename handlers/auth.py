from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from telegram.ext import filters, MessageHandler

from services.firebase import FirebaseClient

class Auth:
    def __init__(self, firebase_client: FirebaseClient):
        self.firebase_db = firebase_client

    def handlers(self) -> list:
        return [
            MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.user_entered_group),
            MessageHandler(filters.ChatType.PRIVATE, self.verify_user),
        ]

    async def user_entered_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Authorize user that entered the group"""
        for member in update.message.new_chat_members:
            user_id = member.id
            chat_id = update.message.chat.id
            if await self.firebase_db.read(f'users/{user_id}') is None:
                await self.firebase_db.update(f'users_unavailable_chats/{user_id}', {chat_id: user_id})
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions.no_permissions()
                )
                await context.bot.send_message(chat_id=update.message.chat_id,
                                               text=(
                                                   f"Привет, @{member.username}, чтобы писать в группу, "
                                                   f"<a href='https://t.me/@t_ad_manager_bot?start'>нажми сюда</a>."
                                               ), parse_mode="HTML")

    async def verify_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user:
            return

        user_id = user.id
        username = user.username

        await self.firebase_db.write(f'users/{user_id}', {username: user_id})

        chats = await self.firebase_db.read(f'users_unavailable_chats/{user_id}')
        if chats:
            for chat_id in chats.values():
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions.all_permissions()
                )
            await self.firebase_db.delete(f'users_unavailable_chats/{user_id}')
        await update.message.reply_text(
            "Спасибо, что написали мне! Теперь вы можете писать в группе."
        )