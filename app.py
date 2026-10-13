"""Точка входа: python app.py

Запускает бота (polling), фоновые задачи: синхронизация доступности
(PMS/Sheets) и отправка напоминаний/follow-up.
"""
import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from bot import build_dp
from config import settings
from db import init_db
from integrations.pms import sync_loop
from services.followups import followup_loop


async def main() -> None:
    if not settings.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан — заполните файл .env (см. .env.example)")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    log = logging.getLogger("app")

    init_db()  # схема + демо-данные при первом запуске
    log.info("База готова: %s", settings.DB_PATH)

    bot = Bot(settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=None))
    dp = build_dp()

    bg = [asyncio.create_task(followup_loop(bot), name="followups"),
          asyncio.create_task(sync_loop(), name="pms-sync")]
    log.info("Бот запускается... CTRL+C — остановка")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        for t in bg:
            t.cancel()


if __name__ == "__main__":
    asyncio.run(main())
