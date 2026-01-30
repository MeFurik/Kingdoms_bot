import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from .config import TG_BOT_TOKEN, REDIS_DSN, ADMIN_IDS, DB_PATH
from .db import init_db
# routers
from .handlers import start as starth
from .handlers import profile as profileh
from .handlers import shop as shoph
from .handlers import admin as adminh

async def main():
    if not TG_BOT_TOKEN:
        raise SystemExit("Set TGBOTTOKEN env var")
    storage = RedisStorage.from_url(REDIS_DSN)
    bot = Bot(token=TG_BOT_TOKEN)
    dp = Dispatcher(bot=bot, storage=storage)

    # attach ADMINIDS to bot object for convenience
    botdata = bot.get('meta', None)
    # we can't set arbitrary attribute on aiogram Bot, so pass ADMINIDS via config usage in handlers

    # register routers
    dp.include_router(starth.router)
    dp.include_router(profileh.router)
    dp.include_router(shoph.router)
    dp.include_router(adminh.router)

    await init_db()
    print("DB initialized. Starting polling...")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())