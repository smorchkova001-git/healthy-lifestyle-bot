import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import signal

from config import BOT_TOKEN
from handlers import router
from middleware import LoggingMiddleware

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Настраиваем middleware, как просят в задании
dp.message.middleware(LoggingMiddleware())
dp.include_router(router)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    asyncio.run(main())