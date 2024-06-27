24 марта 2024
Проба полнотекстового поиска по базе Петрика.
Ищет хорошо.
Надо продумать:
-как вы водить все ролики пагинация или списком илми разбить по тематике
-клавиши поиска по названию, по тексту, точный поиск
-кнопка поиска по корню чел вводит корни
ик нним добавить :* исоединить через & - пример поч:*&кол:*
- как периодически обновлять базу

Пока в базе одна таблица content
Надо добавить остальные
Сделать хэндеры на команды  бота.
19 апреля 2024
--------------------
Вернулся к работе над ботом.
Была идея заменить код бота с базой sqlite3,чтобы использовать тот интерфейс. Просто поменяв код работы с базой на posgresql.
Но скорее сильнее запутаюсь.
Лучше начать делать нового бота на aioram+postgresql. Это будет хороший проект и школа.
П того бота оставить в учебных целях.

Сейчас надо вновь наполнить таблицу актуальными данными  с канала.
Предлагаю создать в базе новую таблицу content_2024 ина ней протестировать.
CREATE TABLE new_table_name AS
SELECT *
FROM existing_table_name;

20 апр  2024
Сделал модуль наполнения базы инфой о видео с канала.
Долго не мог добавить запись в таблицу. Потому, что первичный ключ не был автоинкрементным - это означает,
что значение по умолчанию для этого столбца не установлено или не определено в вашей таблице.
Вероятно, столбец "id" не является автоинкрементным (SERIAL).
Теперь надо продумать, как обновлять базу.
Вот предложение GPT
Получите список всех видео на канале с помощью API YouTube.
Сравните эти видео с видео, которые уже есть в вашей базе данных.
Добавьте только новые видео в вашу базу данных.
Вот пример того, как может выглядеть код на Python:
from googleapiclient.discovery import build
import os
import asyncpg

api_key = 'YOUR_API_KEY'  # Замените YOUR_API_KEY на ваш ключ API

# Параметры подключения к базе данных PostgreSQL
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Функция для подключения к базе данных PostgreSQL
async def connect_to_database():
    return await asyncpg.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )

# Функция для получения списка видео на канале из YouTube API
def get_channel_videos(channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    next_page_token = None

    while True:
        res = youtube.search().list(part='snippet', channelId=channel_id, maxResults=50, pageToken=next_page_token).execute()
        videos.extend(res['items'])
        next_page_token = res.get('nextPageToken')

        if next_page_token is None:
            break

    return videos

# Функция для проверки новых видео и добавления их в базу данных
async def check_and_insert_new_videos(channel_id):
    # Получаем список видео на канале
    channel_videos = get_channel_videos(channel_id)

    # Подключаемся к базе данных
    connection = await connect_to_database()

    try:
        # Получаем список всех видео из базы данных
        existing_videos = await connection.fetch("SELECT url FROM video_table")

        # Сравниваем видео на канале с видео из базы данных
        for video in channel_videos:
            video_id = video['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Если видео не существует в базе данных, добавляем его
            if video_url not in existing_videos:
                await connection.execute("INSERT INTO video_table (url) VALUES ($1)", video_url)
                print(f"Добавлено новое видео: {video_url}")

    finally:
        # Закрываем соединение с базой данных
        await connection.close()

# Пример использования
if __name__ == '__main__':
    channel_id = 'YOUR_CHANNEL_ID'  # Замените YOUR_CHANNEL_ID на ID вашего канала
    asyncio.run(check_and_insert_new_videos(channel_id))

12 мая 2024
Добавил в базу таблицу user и скопировал туда данные на 12 мая 2024.253 польз.
Сделал докер для бота. Получилось не сразу. Спасибо GPT.
Почему-то контейнер перстал работать через VPN.
Надо разобраться с docker compose
вот ответ Крыжановский советовал https://t.me/aiogram_stepik_course/61941/129347
В итоге добавил в /etc/postgresql/{версия}/main/pg_hba.conf еще один IP для доступа к базе

Надо в оглавление сделать случайный показ 50 названий из базы.
Или  сделать пагинацию.
Добавить запись пользователя в базу и его запросов.
--------------------------------------------------------------------
10-11 июня 24 Сделал проверку новых видео на канале. Правда, очень медленно. Возможно на сервере будет работать быстрее.
Теперь надо добавить уведомление админу и возможно польз о выходе новых роликов.
--------------------------------------------------------------------
12 июня в таблицу добавил столбец channel - тег канала для  фильтрации вывода.
Тег канала  добавил и закачал канал Утина. Хочу ему этого бота передать в знак благодарности.
Надо.
Убрать кнопку оглавление.- Сделать например - Случайное видео.
Добавить польз в базу и  отпр сообщение админу. А лучше сделать переключатель типа команды  /admin_off и ввод пароля.