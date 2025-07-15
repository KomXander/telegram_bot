import asyncio
import logging
from aiogram import Bot, Dispatcher

from database import create_table
from handlers import register_handlers
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

register_handlers(dp)

async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
