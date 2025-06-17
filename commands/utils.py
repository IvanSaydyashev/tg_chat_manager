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