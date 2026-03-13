# pip freeze > requirements.txt
# установить pip install -r requirements.txt



import datetime
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from datetime import datetime

# Инициализация бота и диспетчера
bot = Bot(token='7139072705:AAFmOzwzRlSRAIJvcUdem8Tjw0wseGPFJkg')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


    




# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    now = datetime.now()
    await message.answer (f"<i>Привет, я тут!</i>\nСейчас у меня {now}", parse_mode="HTML")
    
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())