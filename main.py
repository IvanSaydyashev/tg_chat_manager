from dotenv import load_dotenv
import os
import logging

from telegram import Update
from telegram.ext import Application

from bot import Bot
from services import LLMService, ConsoleLog, FirebaseLog, FirebaseClient


def main() -> None:
    load_dotenv()

    console_log = ConsoleLog("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_log.set_name("httpx").set_level(logging.WARNING)
    console_log.set_name(__name__)

    firebase_client = FirebaseClient(firebase_url=os.getenv("FIREBASE_DB_URL"), secret=os.getenv("FIREBASE_DB_SECRET"))
    firebase_log = FirebaseLog(firebase_url=os.getenv("FIREBASE_DB_URL"), secret=os.getenv("FIREBASE_DB_SECRET"))

    llm_service = LLMService(console_log=console_log)

    app = Application.builder().token(os.getenv("TOKEN")).build()

    bot = Bot(llm_service=llm_service, firebase_client=firebase_client, firebase_log=firebase_log, console_log=console_log)

    app.add_error_handler(bot.error_handler)

    for handler in bot.handlers():
        app.add_handler(handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
