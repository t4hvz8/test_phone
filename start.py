# pip freeze > requirements.txt
# установить pip install -r requirements.txt


import datetime
import asyncio
import sqlite3
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.input_file import FSInputFile
from aiogram.types import Message

from datetime import datetime

# Инициализация бота и диспетчера
bot = Bot(token='7139072705:AAFmOzwzRlSRAIJvcUdem8Tjw0wseGPFJkg', timeout=300)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создаем папку temp, если её нет
if not os.path.exists('temp'):
    os.makedirs('temp')
    
class user_message(StatesGroup):
    save = State()

with sqlite3.connect('test.db') as con:
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS data(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            us_idtg VARCHAR (20), 
            us_text VARCHAR (40), 
            us_blob BLOB,
            us_datetime VARCHAR (30)
            )''')
    con.commit()    

print ('Старт бота')
# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    if state:
        await state.clear()
    user_id = message.from_user.id
    name = message.chat.first_name
    print(f"{user_id} нажал старт")
    await state.set_state(user_message.save)
    await message.answer (f"Привет, {name}!\nВводи мне текст или фото и я сохраню", parse_mode="HTML")

@dp.message(Command("file"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.chat.first_name
    print(f"{user_id} запросил файл БД")
    if state:
        await state.clear()
    file_path = "test.db"
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        print(f"размер файла {size_mb}mb. Начинаю отправку")
        document = FSInputFile(file_path)
        await bot.send_document(chat_id=user_id, document=document, caption="файл базы", timeout=300, parse_mode="HTML")
    except FileNotFoundError:
        await message.answer (f"Привет, {name}!\nБеда бедовая, файл не найдет", parse_mode="HTML")
    except OSError as e:
        await message.answer (f"Привет, {name}!\nБеда бедовая, ошибка {e}", parse_mode="HTML")
    

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "OK":
        await callback_query.answer()
        if state:
            await state.clear()
        print(f"{user_id} нажал ОК")
        name = callback_query.from_user.first_name
        await state.set_state(user_message.save)
        await bot.send_message(
            chat_id=user_id,  
            text=f"Привет, {name}!\nВводи мне текст или фото и я сохраню",
            parse_mode="HTML"
        )

@dp.message(user_message.save)
async def finish_task(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    if message.photo:
        print(f"{user_id} прислал картинку")
        photo = message.photo[-1]  # Берем фото с самым высоким разрешением
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        download_path = os.path.join('temp', f"image_{user_id}_{datetime.now().timestamp()}.jpg")
        await bot.download_file(file_path, destination=download_path)
        description = ""
        text = "✅ Принято, фото записано, можно продолжать"
        if message.caption:
            # Есть описание к фото - сохраняем описание в .txt
            description = message.caption
            print(f"Описание: {description}")
            text = "✅ Принято, фото С ОПИСАНИЕМ записано, можно продолжать"
        print(f"Фото сохранено временно: {download_path}")
        with open(download_path, 'rb') as file:
            photo_data = file.read()
        with sqlite3.connect('test.db') as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO data (us_idtg, us_text, us_blob, us_datetime) VALUES (?, ?, ?, ?)', 
                (user_id, description, photo_data, current_time)
            )
            con.commit()
        print(f"Записал картинку и описание в БД")
        os.remove(download_path)
        print(f"Временный файл удален")
        # Отправляем подтверждение
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="OK", callback_data="OK")) 
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=board.as_markup()
        )
   
    elif message.text and not message.text.startswith('/'):
        print(f"{user_id} прислал текст")
        description = message.text
        with sqlite3.connect('test.db') as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO data (us_idtg, us_text, us_datetime) VALUES (?, ?, ?)', 
                (user_id, description, current_time)
            )
            con.commit()
        print(f"текст записан")
                
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="OK", callback_data="OK")) 
        await bot.send_message(
            chat_id=user_id,
            text="✅ Принято, текст записан, можно продолжать",
            parse_mode="HTML",
            reply_markup=board.as_markup()
        )

    # Обработка других типов сообщений (видео, документы и т.д.)
    elif not message.text and not message.photo:
        await message.answer("Я принимаю только текст и изображения 😊")

def is_image_message(message: types.Message) -> bool:
    return bool(message.photo)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
