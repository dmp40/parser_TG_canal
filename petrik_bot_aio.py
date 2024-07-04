'''Ушел в поход 04,07, 24
cron работает  базу обновляет но не приходит уведомление'''
import asyncio
import asyncpg
import os
import logging
from aiogram import Bot, Dispatcher, types, F
#from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
#from aiogram.utils import executor
import nats
import ast
import aiocron
from nats.errors import TimeoutError
from video_subtitr_API import  check_and_add_new_videos ,on_new_video


print('запуск бота')
# Планируем задачу на каждый день в 15:40
@aiocron.crontab("*/30  * * * *")
async def scheduled_check():
    logging.info("Запуск проверки новых видео")
    try:
        print('сработал crontab')
        await check_and_add_new_videos("UCY649zJeJVhhJa-rvWThZ2g", "utin")
        #await  on_new_video("555555", "Новое видео в боте23 ", "channel_Petrik24")
    except Exception as e:
        logging.error(f"Error during scheduled check: {e}")

# Установка уровня логирования
logging.basicConfig(level=logging.DEBUG)

# Загрузка переменных окружения из файла .env
from dotenv import load_dotenv

load_dotenv()
admin_id = "5843027547"  # Mik

# Параметры подключения к базе данных PostgreSQL
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Токен вашего бота
bot_token = os.getenv('TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=bot_token) # токен надо поменять тк пропал аккаунт в телеге с этим токеном
dp = Dispatcher()

# обработка собщений из NATS
async def message_handler(msg):
    #message = eval(msg.data.decode())
    msg_str = msg.data.decode('utf-8')
    message = ast.literal_eval(msg_str)
    video_id = message['video_id']
    video_title = message['video_title']

    await send_notification(video_id, video_title)

# Функция отправки уведомления
async def send_notification(video_id,  video_title):
    # Логика отправки уведомления пользователю
    # Здесь вы можете явно указать chat_id для двух пользователей для отладки
    selected_chat_ids = ['213697976', '5843027547']#,'297769549']  # [дима,Мик,Ира]Замените на реальные chat_id
    print(f"Sending notification to user  about video  {video_id} {video_title}")
    for select_user_id in selected_chat_ids:
        #await message.answer(f"{title['title'][:300]}\n<a href='https://youtube.com/watch?v={title['url']}'>Смотреть видео</a>",
            #parse_mode="HTML", disable_web_page_preview=True)
        await bot.send_message(select_user_id, f"Новые видео на канале Доктор Утин: {video_id}<a href='https://www.youtube.com/watch?v={video_title}'> Смотреть видео</a>",parse_mode="HTML", disable_web_page_preview=True)


# Функция для начала потребления сообщений
async def start_nats_listener():
    nc = await nats.connect("nats://localhost:4222")
    await nc.subscribe("new_videos", cb=message_handler)
    # nc = await nats.connect("nats://localhost:4222")
    # js = nc.jetstream()
    # await js.pull_subscribe("new_videos", cb=message_handler)


# Функция для подключения к базе данных PostgreSQL
async def connect_to_database():
    return await asyncpg.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
#обработка запроса из нескольких слов
def process_string(input_string):
    if '"' in input_string:  # Если есть кавычки в строке
        input_string = input_string.replace('"', '')  # Убираем кавычки из строки
        input_string = input_string.replace(' ', '&')  # Заменяем пробелы на &
    else:
        words = input_string.split()  # Разбиваем строку на слова по пробелу
        result = ""  # Будущая строка с результатом

        for i in range(len(words)):
            if i == len(words) - 1:  # Если это последнее слово
                result += f"{words[i]}:*"  # Добавляем слово и ":*"
            else:
                result += f"{words[i]}:*&"  # Добавляем слово и ":*&"

        return result
    return input_string


# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def send_welcome(message: types.Message):
    # Создаем клавиатуру с кнопкой "Поиск"
    button_1 = KeyboardButton(text='ВидеоМикс 🔄')
    button_2 = KeyboardButton(text='Поиск 👀')
    # Создаем объект клавиатуры, добавляя в него кнопки
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2]], resize_keyboard=True)



    await message.reply("Привет! Я помогу найти видео с канала  'Доктор Утин'.", reply_markup=keyboard)

# Этот хэндлер будет срабатывать на ответ Поиск
@dp.message(F.text == 'Поиск 👀')
async def process_dog_answer(message: Message):
    await message.answer(text='Введите 1-2  слова для поиска.\nМожно  без окончаний: \n'
                              'например: бол гол\n'
                              'Покажет видео про головную боль\n'
                              'Для точного поиска наберите запрос в кавычках\n')

# Этот хэндлер будет срабатывать на ответ оглавление
@dp.message(F.text == 'ВидеоМикс 🔄')
async def send_titles(message: types.Message):
    connection = None
    try:
        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Получаем все заголовки из базы данных
        titles = await connection.fetch("SELECT title, url FROM content_20_04_2024 ORDER BY RANDOM() LIMIT 3")
        num = 0
        # Отправляем заголовки пользователю
        await message.answer('Три случайных видео')
        if titles:
            for title in titles:
                num += 1

                print(num)
                await message.answer(f"{title['title'][:300]}\n<a href='https://youtube.com/watch?v={title['url']}'>Смотреть видео</a>",
                                     parse_mode="HTML", disable_web_page_preview=True)

                await message.answer('-----------------------------------')
                # Добавляем задержку перед отправкой следующего сообщения (в данном случае 1 секунду)
                await asyncio.sleep(0.5)
                if num == 10:
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
        search_word = process_string(message.text)
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
            'StartSel=<u><i>🔻, StopSel=</i></u>🔻, MaxWords=35, MinWords=15,HighlightAll=false')


             title, url, duration FROM content_20_04_2024
             WHERE to_tsvector('russian', title) @@ to_tsquery('russian', $1)
        """



        search_results = await connection.fetch(search_query, search_word)
        print(f'Найдено - {search_results}')
        search_num= len(search_results)
        if search_num > 0: await message.answer(f'Найдено {search_num} видео')
        # Отправляем результаты поиска пользователю
        if search_results:
            for result in search_results:
                #await message.answer(f"{result['title'][:200]}\n{result['url']}", parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
                await message.answer(f"{result['title'][:200]}\n<a href='https://youtube.com/watch?v={result['url']}'>Видео</a>  ⌛{(result['duration']).replace('.',':')}",
                                     parse_mode="HTML", disable_web_page_preview=True)
                #await message.answer('◽◽◽◽◽◽◽◽◽')
                await message.answer('______________')
        else:
            await message.answer("По вашему запросу ничего не найдено.")
    except IndexError:
        await message.reply("Вы не ввели слово для поиска.")

    except asyncpg.exceptions.PostgresError as pg_error:
        # обработка ошибок, связанных с PostgreSQL
        print("Ошибка PostgreSQL: %s", pg_error)
        await message.reply(f"Ошибка PostgreSQL:{pg_error}")
    except Exception as e:
        logging.error("Error occurred: %s", e)
    finally:
    # Закрываем соединение с базой данных
        if connection:
            await connection.close()


async def aiogram_bot():
    # Запуск запланированных задач

    #scheduled_check.start()
    await asyncio.gather(dp.start_polling(bot), start_nats_listener())

# Запуск бота
if __name__ == '__main__':
    #dp.run_polling(bot)
    #asyncio.run(aiogram_bot())  При таком запуске  aiocron не работает

    loop = asyncio.get_event_loop()
    loop.run_until_complete(aiogram_bot())
