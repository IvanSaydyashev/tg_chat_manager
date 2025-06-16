import logging
import uuid
from abc import abstractmethod
from typing import Protocol, Any, Self
from enum import Enum

from firebase_admin.exceptions import FirebaseError
from time import time
from pydantic import BaseModel

from services.firebase import FirebaseClient

class Log(Protocol):
    @abstractmethod
    async def awrite(self, status: Any, msg: Any) -> None:
        """Async write log message."""
        pass

    @abstractmethod
    def write(self, status: Any, msg: Any) -> None:
        """Write log message."""
        pass


class FirebaseAction(Enum):
    BAN = "BAN"
    UNBAN = "UNBAN"
    MUTE = "MUTE"
    UNMUTE = "UNMUTE"


class FirebaseLogFormat(BaseModel):
    """Firebase Realtime Log Formatter."""
    chat_id: int
    user_id: int
    message: str
    reason: str


class FirebaseLog(FirebaseClient):
    """Firebase Realtime DB Logs."""
    async def awrite(self, status: Any, msg: Any) -> None:
        """
        Write log message in Firebase Runtime DB.
        msg should be 'FireBaseLogFormat' class instance.
        status should be 'FirebaseAction' class instance.
        """
        log = FirebaseLogFormat.model_validate_json(msg)
        event = uuid.uuid4()
        ref = self.db.reference(f"logs/{log.chat_id}/{event}")
        timestamp = int(time() * 1000)
        data = {
            "timestamp": timestamp,
            "user_id": log.user_id,
            "message": log.message,
            "reason": log.reason,
        }

        match status:
            case FirebaseAction.BAN:
                data |= {"action": FirebaseAction.BAN.value}
            case FirebaseAction.UNBAN:
                data |= {"action": FirebaseAction.UNBAN.value}
            case FirebaseAction.MUTE:
                data |= {"action": FirebaseAction.MUTE.value}
            case FirebaseAction.UNMUTE:
                data |= {"action": FirebaseAction.UNMUTE.value}
            case _:
                raise RuntimeError(f"Unexpected Firebase Log Format: {status}")

        try:
            ref.set(data)
        except FirebaseError as e:
            raise Exception(f"FirebaseError: {e}")

    def write(self, status: Any, msg: Any) -> None:
        """
        Write log message in Firebase Runtime DB.
        msg should be 'FireBaseLogFormat' class instance.
        status should be 'FirebaseAction' class instance.
        """
        log = FirebaseLogFormat.model_validate_json(msg)
        event = uuid.uuid4()
        ref = self.db.reference(f"logs/{log.chat_id}/{event}")
        timestamp = int(time() * 1000)
        data = {
            "timestamp": timestamp,
            "user_id": log.user_id,
            "message": log.message,
            "reason": log.reason,
        }

        match status:
            case FirebaseAction.BAN:
                data |= {"action": FirebaseAction.BAN.value}
            case FirebaseAction.UNBAN:
                data |= {"action": FirebaseAction.UNBAN.value}
            case FirebaseAction.MUTE:
                data |= {"action": FirebaseAction.MUTE.value}
            case FirebaseAction.UNMUTE:
                data |= {"action": FirebaseAction.UNMUTE.value}
            case _:
                raise RuntimeError(f"Unexpected Firebase Log Format: {status}")

        try:
            ref.set(data)
        except FirebaseError as e:
            raise Exception(f"FirebaseError: {e}")


class ConsoleLog(Log):
    """Console Log."""

    def __init__(self, formater: str, level: int = logging.INFO, name: str = "__main__") -> None:
        """
        formater: format string for log message
        level: log level INFO by default
        """
        logging.basicConfig(format=formater, level=level)
        self.formater = formater
        self.logger = logging.getLogger(name)

    def set_name(self, name: str) -> Self:
        """alias for logging.getLogger(name)"""
        self.logger = logging.getLogger(name)
        return self

    def with_name(self, name: str) -> Self:
        """Creates a new instance of ConsoleLog with a different logger name."""
        return ConsoleLog(formater=self.formater, level=self.logger.level, name=name)

    def set_level(self, level: int) -> Self:
        """alias for logging.setLevel(level)"""
        self.logger.setLevel(level)
        return self

    async def awrite(self, status: Any, msg: Any) -> None:
        """Write log message in console."""
        match status:
            case logging.INFO:
                self.logger.info(msg)
            case logging.WARNING:
                self.logger.warning(msg)
            case logging.ERROR:
                self.logger.error(msg)
            case logging.CRITICAL:
                self.logger.critical(msg)
            case logging.NOTSET:
                self.logger.debug(msg)
            case _:
                raise RuntimeError(f"Unexpected Console Log Format: {status}")

    def write(self, status: Any, msg: Any) -> None:
        """Async write log message in console."""
        match status:
            case logging.INFO:
                self.logger.info(msg)
            case logging.WARNING:
                self.logger.warning(msg)
            case logging.ERROR:
                self.logger.error(msg)
            case logging.CRITICAL:
                self.logger.critical(msg)
            case logging.NOTSET:
                self.logger.debug(msg)
            case _:
                raise RuntimeError(f"Unexpected Console Log Format: {status}")
