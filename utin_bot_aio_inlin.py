import asyncio
import asyncpg
import os
import logging
from aiogram import Bot, Dispatcher, types, F
#from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message



# Установка уровня логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
from dotenv import load_dotenv

load_dotenv()

# Параметры подключения к базе данных PostgreSQL
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Токен вашего бота
bot_token = os.getenv('TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=bot_token)
dp = Dispatcher()
# словарь для кнопок
KB: dict[str, str] = {
    'search': 'Поиск 👀',
    'context': 'Оглавление 🗺'
}
# Создаем объекты инлайн-кнопок
big_button_1 = InlineKeyboardButton(
    text='Поиск 👀',
    callback_data='big_button_1_pressed'
)

big_button_2 = InlineKeyboardButton(
    text='Оглавление 🗺',
    callback_data='big_button_2_pressed'
)

# Создаем объект инлайн-клавиатуры
keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[big_button_1],
                     [big_button_2]]
)

# Функция для подключения к базе данных PostgreSQL
async def connect_to_database():
    return await asyncpg.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )


# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def send_welcome(message: types.Message):
    # # Создаем клавиатуру с кнопкой "Поиск"
    # button_1 = KeyboardButton(text= KB['context'])
    # button_2 = KeyboardButton(text=KB['search'])
    # # Создаем объект клавиатуры, добавляя в него кнопки
    # keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2]], resize_keyboard=True)
    await message.reply("Привет! Я бот, который выводит содержание полей title из базы данных.", reply_markup=keyboard)

# Этот хэндлер будет срабатывать на ответ Поиск
#@dp.message(F.text == 'Поиск 👀')
@dp.message(F.text.in_([KB['search']]))
async def process_dog_answer(message: Message):
    await message.answer(text='Введите 1-2 слова для поиска' )
    try:
        # Получаем слово для поиска из сообщения пользователя
        search_word = message.text

        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Выполняем полнотекстовый поиск в базе данных по полю title
        search_query = """
               SELECT title, post_id FROM post_canal
               WHERE to_tsvector('russian', title) @@ to_tsquery('russian', $1)
           """
        search_results = await connection.fetch(search_query, search_word)

        # Отправляем результаты поиска пользователю
        if search_results:
            for result in search_results:
                await message.answer(f"{result['title'][:200]}\n{result['post_id']}", parse_mode=None,
                                     disable_web_page_preview=True)
                await message.answer('◽◽◽◽◽◽◽◽◽')
        else:
            await message.reply("По вашему запросу ничего не найдено.")
    except IndexError:
        await message.reply("Вы не ввели слово для поиска.")
    except Exception as e:
        logging.error("Error occurred: %s", e)
    finally:
        # Закрываем соединение с базой данных
        await connection.close()


    #await send_echo(search)

# Этот хэндлер будет срабатывать на ответ оглавление
@dp.message(F.text == 'Оглавление 🗺')
async def send_titles(message: types.Message):
    connection = None
    try:
        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Получаем все заголовки из базы данных
        titles = await connection.fetch("SELECT title, post_id FROM post_canal")
        num = 0
        # Отправляем заголовки пользователю
        if titles:
            for title in titles:
                num += 1

                print(num)
                await message.answer(f"{title['title'][:200]}\n{title['post_id']}", parse_mode=None, disable_web_page_preview=True)
                await message.answer('-----------------------------------')
                # Добавляем задержку перед отправкой следующего сообщения (в данном случае 1 секунду)
                await asyncio.sleep(0.5)
                if num == 100:
                    break

        else:
            await message.reply("Заголовки не найдены в базе данных.")
    except Exception as e:
        logging.error("Error occurred: %s", e)
    finally:
        # Закрываем соединение с базой данных
        if connection:
            await connection.close()

# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_1_pressed'
@dp.callback_query(F.data == 'big_button_1_pressed')
async def process_button_1_press(callback: CallbackQuery):
    if callback.message.text != 'Была нажата БОЛЬШАЯ КНОПКА 1':
        await callback.message.edit_text(
            text='Была нажата БОЛЬШАЯ КНОПКА 1',
            reply_markup=callback.message.reply_markup
        )
    await callback.answer(text='Ура! Нажата кнопка Поиск')


# Этот хэндлер будет срабатывать на апдейт типа CallbackQuery
# с data 'big_button_2_pressed'
@dp.callback_query(F.data == 'big_button_2_pressed')
async def process_button_2_press(callback: CallbackQuery):
    if callback.message.text != 'Была нажата БОЛЬШАЯ КНОПКА 2':
        await callback.message.edit_text(
            text='Была нажата БОЛЬШАЯ КНОПКА 2',
            reply_markup=callback.message.reply_markup
        )
    await callback.answer(text='Ура! Нажата кнопка Оглавление')



# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
#@dp.message()
#async def send_echo(message: Message):







# Запуск бота
if __name__ == '__main__':
    dp.run_polling(bot)
