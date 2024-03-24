import telebot
import asyncpg
import os
import asyncio

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

# Инициализация бота
bot = telebot.TeleBot(bot_token)


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
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот, который выводит содержание полей title из базы данных.")


# Обработчик команды /titles
@bot.message_handler(commands=['titles'])
async def send_titles(message):
    try:
        # Подключаемся к базе данных
        connection = await connect_to_database()

        # Получаем все заголовки из базы данных
        titles = await connection.fetch("SELECT title FROM post_canal")

        # Отправляем заголовки пользователю
        if titles:
            for title in titles:
                await bot.send_message(message.chat.id, title['title'])
        else:
            await bot.send_message(message.chat.id, "Заголовки не найдены в базе данных.")
    except Exception as e:
        print("Error:", e)
    finally:
        # Закрываем соединение с базой данных
        await connection.close()


# Запуск бота
bot.polling()

# # Запуск бота в асинхронном режиме
# async def main():
#     await bot.polling()
#
# # Запуск бота
# asyncio.run(main())
