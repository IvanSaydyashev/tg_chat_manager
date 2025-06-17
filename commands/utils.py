from telegram import Update

from handlers.error import InvalidDurationFormatError
import re

def parse_duration(s: str):
    match = re.match(r"(\d+)([mhd])", s)
    if not match:
        raise InvalidDurationFormatError("Неправильный формат времени. Используй, например: 10m, 1h, 2d")

    value, unit = match.groups()
    value = int(value)
    return {
        "m": value * 60,
        "h": value * 3600,
        "d": value * 86400
    }[unit]

async def is_admin(update: Update):
    """Check if the user that sent the message is an admin in the chat."""
    user_id = update.effective_user.id
    member = await update.effective_chat.get_member(user_id)
    return member.status in ['administrator', 'creator']