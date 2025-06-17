class BaseError(Exception):
    """Base error class."""

class UserNotRepliedError(BaseError):
    """Ошибка, если не ответили на сообщение."""


class InvalidDurationFormatError(BaseError):
    """Ошибка, если введён некорректный формат времени."""

class MissingReasonError(BaseError):
    """Ошибка, если не указано причину."""

class MissingDurationError(BaseError):
    """Ошибка, если не указано время для временного бана."""

class UserIsAdminError(BaseError):
    """Ошибка, если пользователь является администратором."""