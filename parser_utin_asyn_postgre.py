'''ПАрсим канал доктора Утина
запись в базу utin_post на PostgreSQL
Надо настроить полнотекстовый поиск
Пагинацию содержания
Деплоить на VPS




'''
import asyncio
import os
import re
import asyncpg
#from datetime import datetime
from telethon.sync import TelegramClient
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение значений переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Параметры подключения к базе данных PostgreSQL
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Путь к каналу Telegram
channel_username = '@doctorutin'     #'@aiogram_stepik_course'     # '@drmyasnikov''@doctorutin' #'@drmyasnikov' aiogram_stepik_course/61941

# Функция для инициализации и запуска клиента Telegram
async def initialize_telegram_client():
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    return client

# Функция для подключения к базе данных PostgreSQL
async def connect_to_database():
    return await asyncpg.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )

# Берем первые 100 символов, если нет заголовка поста
def get_first_100_chars(text):
    # Получаем первые 100 символов текста
    first_100_chars = text[:100]

    # Находим индекс последнего пробела перед первыми 100 символами
    last_space_index = first_100_chars.rfind(' ')

    # Если последний пробел найден
    if last_space_index != -1:
        # Получаем текст до последнего пробела включительно
        first_100_chars = first_100_chars[:last_space_index]+"..."

    return first_100_chars

# Функция для получения текстовых постов из канала
async def get_text_posts(client):
    text_posts = []
    match_none = 0
    num = 0
    async for message in client.iter_messages(channel_username):
        if message.text:
            num += 1
            print(f'найдено {num}')
            match = message.text # re.match(r'^.*?(?=\n)', message.text, re.DOTALL)
            # для парсинга чата про aiogram
            #post_info = {'title': match, 'url': f'https://t.me/aiogram_stepik_course/61941/{str(message.id)}'}
            # для парсинга канла  доктора Утина: https://t.me/doctorutin/939
            post_info = {'title': match, 'url': f'https://t.me/doctorutin/{str(message.id)}'}
            text_posts.append(post_info)
            #print(post_info)
            if num == 70000:
                return text_posts
            # if match:
            #     first_sentence = match.group(0)
            #     if first_sentence.strip():
            #         #Сменить url https://t.me/aiogram_stepik_course/61941  https://t.me/doctorutin/
            #         post_info = {'title': first_sentence.strip(), 'url': f'https://t.me/aiogram_stepik_course/61941/{str(message.id)}'}
            #         text_posts.append(post_info)
            # else:
            #     match_none += 1
            #     #print(f'пустых заголовков-{match_none}  Id-{message.id}\n {message.text}')
            #     text_100 = get_first_100_chars(message.text)
            #     post_info = {'title': text_100, 'url': f'https://t.me/doctorutin/{message.id}'}
            #     text_posts.append(post_info)
    return text_posts

# Функция для добавления постов в базу данных PostgreSQL
# async def add_posts_to_database(connection, posts):
#     async with connection.transaction():
#         for post in posts:
#             await connection.execute('''INSERT INTO stepik_post (title, post_id) VALUES ($1, $2)''', post['title'], post['url'])
# Функция для добавления постов в базу данных PostgreSQL
'''Этот код представляет функцию для добавления постов в базу данных PostgreSQL.
Давайте рассмотрим его по шагам:
async def add_posts_to_database(connection, posts):: 
Объявляет асинхронную функцию add_posts_to_database, которая принимает два аргумента: connection (соединение с базой данных) и posts (список постов, которые нужно добавить в базу данных).

async with connection.transaction()::
Начинает асинхронную транзакцию с базой данных, что гарантирует целостность данных.

for i in range(0, len(posts), 500)::
Цикл, который проходит по списку постов в порциях по 500 постов за раз.

chunk = posts[i:i+500]: Выбирает очередную порцию постов размером до 500 постов.

values = [(post['title'], post['url']) for post in chunk]:
Для каждого поста в текущей порции создается кортеж значений, содержащий заголовок и URL поста.

await connection.executemany(INSERT INTO stepik_post (title, post_id) VALUES ($1, $2), values):
Выполняет массовую вставку данных в таблицу stepik_post. Используется параметризованный запрос, 
который вставляет значения заголовка и URL каждого поста в соответствующие столбцы таблицы.'''

async def add_posts_to_database(connection, posts):
    async with connection.transaction():
        print("запись в базу")
        for i in range(0, len(posts), 500):
            chunk = posts[i:i+500]
            values = [(post['title'], post['url']) for post in chunk]
            # строка для парсинга чата про aiogram
            #await connection.executemany('''INSERT INTO stepik_post (title, post_id) VALUES ($1, $2)''', values)
            # строка для парсинга канала Доктор Утин
            await connection.executemany('''INSERT INTO post_canal (title, post_id) VALUES ($1, $2)''', values)


# Асинхронная функция для выполнения основного функционала
async def main():
    client = await initialize_telegram_client()
    connection = await connect_to_database()
    text_posts = await get_text_posts(client)
    for i in range(0, len(text_posts), 500):
        chunk = text_posts[i:i + 500]
        await add_posts_to_database(connection, chunk)
    #await add_posts_to_database(connection, text_posts)
    await client.disconnect()
    await connection.close()

# Запуск основной функции в асинхронном контексте
asyncio.run(main())
