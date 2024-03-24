import asyncio
import asyncpg
import os
import logging
from aiogram import Bot, Dispatcher, types, F
#from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)


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
    # Создаем клавиатуру с кнопкой "Поиск"
    button_1 = KeyboardButton(text='Оглавление 🗺')
    button_2 = KeyboardButton(text='Поиск 👀')
    # Создаем объект клавиатуры, добавляя в него кнопки
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2]], resize_keyboard=True)


    await message.reply("Привет! Я бот, который выводит содержание полей title из базы данных.", reply_markup=keyboard)

# Этот хэндлер будет срабатывать на ответ Поиск
@dp.message(F.text == 'Поиск 👀')
async def process_dog_answer(message: Message):
    await message.answer(text='Введите 1-2 слова для поиска' )

# Этот хэндлер будет срабатывать на ответ оглавление
@dp.message(F.text == 'Оглавление 🗺')
async def send_titles(message: types.Message):
    connection = None
    try:
        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Получаем все заголовки из базы данных
        titles = await connection.fetch("SELECT title, url FROM content")
        num = 0
        # Отправляем заголовки пользователю
        if titles:
            for title in titles:
                num += 1

                print(num)
                await message.answer(f"{title['title'][:200]}\n<a href='{title['url']}'>Смотреть видео</a>",
                                     parse_mode='HTML', disable_web_page_preview=True)
                await message.answer('-----------------------------------')
                # Добавляем задержку перед отправкой следующего сообщения (в данном случае 1 секунду)
                await asyncio.sleep(0.5)
                if num == 300:
                    break

        else:
            await message.reply("Заголовки не найдены в базе данных.")
    except Exception as e:
        logging.error("Error occurred: %s", e)
    finally:
        # Закрываем соединение с базой данных
        if connection:
            await connection.close()


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    try:
        # Получаем слово для поиска из сообщения пользователя
        search_word = message.text
        print(f'ищем {search_word}')

        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Выполняем полнотекстовый поиск в базе данных по полю title
        # search_query = """
        #     SELECT title, url FROM content
        #     WHERE to_tsvector('russian', post) @@ to_tsquery('russian', $1)
        # """
        # Запрос с показом текста с выделением и сопутствующими словами
        search_query = """
             SELECT  ts_headline(
            'russian',
            title,
            to_tsquery('russian', $1),
            'StartSel=<u><i>🔻, StopSel=</i></u>🔻, MaxWords=35, MinWords=15,HighlightAll=true')


             title, url FROM content
             WHERE to_tsvector('russian', title) @@ to_tsquery('russian', $1)
        """



        search_results = await connection.fetch(search_query, search_word)
        print(f'Найдено - {search_results}')
        # Отправляем результаты поиска пользователю
        if search_results:
            for result in search_results:
                #await message.answer(f"{result['title'][:200]}\n{result['url']}", parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
                await message.answer(f"{result['title'][:200]}\n<a href='{result['url']}'>Видео</a>",
                                     parse_mode="HTML", disable_web_page_preview=True)
                #await message.answer('◽◽◽◽◽◽◽◽◽')
                await message.answer('______________')
        else:
            await message.answer("По вашему запросу ничего не найдено.")
    except IndexError:
        await message.reply("Вы не ввели слово для поиска.")
    except Exception as e:
        logging.error("Error occurred: %s", e)
    finally:
    # Закрываем соединение с базой данных
        if connection:
            await connection.close()






# Запуск бота
if __name__ == '__main__':
    dp.run_polling(bot)
