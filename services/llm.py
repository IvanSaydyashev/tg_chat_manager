from functools import lru_cache

from together import AsyncTogether

import logging
import dotenv
import os

from services.log import ConsoleLog

class LLMService:
    def __init__(self, console_log: ConsoleLog) -> None:
        dotenv.load_dotenv()
        self.console_logs = console_log.with_name(__name__)
        try:
            self.client = AsyncTogether(api_key=os.getenv('LLM_API_KEY'))
            self.console_logs.write(status=logging.INFO, msg="LLM initialized successfully")
        except Exception as e:
            self.console_logs.write(status=logging.ERROR, msg=f"LLM initialization failed: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}") from e

    @lru_cache(maxsize=512)
    async def validate_message_cached(self, message: str) -> (str, str):
        return await self.validate_message(message)

    async def validate_message(self, message: str) -> (str, str):
        self.console_logs.write(status=logging.INFO, msg="Validating message...")
        response = await self.client.chat.completions.create(
            model="lgai/exaone-3-5-32b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "Представь, что ты модератор канала."
                               "Твоя задача модерация введенного сообщения и его проверка на спам, ненормативную лексику,"
                               "оскорбления, религиозные риски, публичный вред, агрессию, вредоносность и политику."
                               "Сообщения, содержащие восхваление стран, одобряющие нацизм, неонацизм, агрессию на рассовой почве "
                               "НЕ ДОЛЖНЫ пройти модерацию."
                               "Например: слава + <страна/политический деятель> НЕ ДОЛЖНО ПРОХОДИТЬ МОДЕРАЦИЮ"
                               "Все, кроме вышеперечисленного, явялется безопасным и должно проходить модерацию."
                               "Не превышай свои полномочия. Модерацию не должен проходить ИСКЛЮЧИТЕЛЬНО вредоносный контент."
                               "Если по контексту сообщения не понятно, является ли содержимое вредоносным контентом, то "
                               "это сообщение БЕЗОПАСНО и ДОЛЖНО проходить модерацию."
                               "выводи ответ СТРОГО в этом формате:"
                               "если прошло модерацию: safe"
                               "Если не прошло: unsafe Reason, вместо Reason напиши что именно не прошло модерацию."
                },
                {
                    "role": "user",
                    "content": f"{message}"
                }
            ],
        )
        llm_response = response.choices[0].message.content
        await self.console_logs.awrite(status=logging.INFO, msg=f"LLM response: {llm_response}")
        parsed_response = llm_response.split()
        status, reason = parsed_response[0], ' '.join(parsed_response[1:])
        return status, reason
