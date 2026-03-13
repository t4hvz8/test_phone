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
bot = Bot(token='7139072705:AAFmOzwzRlSRAIJvcUdem8Tjw0wseGPFJkg')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

    
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
    print(f"{user_id} запросил файл БД")
    if state:
        await state.clear()
    path = f'test.db'
    document = FSInputFile(path)
    await bot.send_document(chat_id=user_id, document=document, caption="файл базы", parse_mode="HTML")

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
        await bot.send_message(
            chat_id=user_id,  
            text=f"Привет, {name}!\nВводи мне текст или фото и я сохраню",
            parse_mode="HTML"
        )

@dp.message(user_message.save)
async def finish_task(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    if is_image_message(message):
        print(f"{user_id} прислал картинку")
        # Пользователь прислал фото
        if message.caption:
            print(f"{user_id} у картинки есть описание")
            # Есть описание к фото - сохраняем описание в .txt
            description = message.caption
            with sqlite3.connect('test.db') as con:
                cur = con.cursor()
                cur.execute(f'INSERT INTO data (us_idtg, us_text, us_datetime) VALUES (?, ?, ?)', (user_id, description, current_time))
                con.commit()
                print("Записал описание в БД")
        # Сохраняем фото
        photo = message.photo[-1]  # Берем фото с самым высоким разрешением
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        download_path = os.path.join('temp', f"image_{user_id}.jpg")
        await bot.download_file(file_path, destination=download_path)
        done = save_finish_photo(user_id)
        if done:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="OK", callback_data="OK")) 
            await bot.send_message(
                chat_id=user_id,
                text="Принято, записано, можно продолжать",
                parse_mode="HTML",
                reply_markup=board.as_markup()
            )
        else:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="OK", callback_data="OK")) 
            await bot.send_message(
                chat_id=user_id,
                text="<b>НЕ ЗАПИСАНО</b>, можно продолжать",
                parse_mode="HTML",
                reply_markup=board.as_markup()
            )
    elif message.text:
        print(f"{user_id} прислал текст")
        description = message.text
        with sqlite3.connect('test.db') as con:
            cur = con.cursor()
            cur.execute(f'INSERT INTO data (us_idtg, us_text, us_datetime) VALUES (?, ?, ?)', (user_id, description, current_time))
            con.commit()
            print(f"текст записан")
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="OK", callback_data="OK")) 
        await bot.send_message(
            chat_id=user_id,
            text="Принято, записано, можно продолжать",
            parse_mode="HTML",
            reply_markup=board.as_markup()
        )

def save_finish_photo(user_id):
    image_path = f'temp/image_{user_id}.jpg'
    with open(image_path, 'rb') as file:
        photo = file.read()
    with sqlite3.connect(f'test.db') as con:
        cur = con.cursor()
        done = cur.execute(f'INSERT INTO data (us_blob) VALUES (?)', [photo])
        con.commit()
        
    if done:
        print("Записал картинку в БД")
        return True
    else:
        print("Не записал картинку в БД")
        return False









def is_image_message(message: types.Message) -> bool:
    return bool(message.photo)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())