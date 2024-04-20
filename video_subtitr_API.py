''' Модуль заполнения базы  данными о видео с канала
Канал добавляется по ID
'''

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import psycopg2
import sqlite3
import asyncio
import asyncpg

# Загрузка переменных окружения из файла .env
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('API_YOUTUBE')
youtube = build('youtube', 'v3', developerKey=api_key)

# Параметры подключения к базе данных PostgreSQL
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Функция для подключения к базе данных PostgreSQ
def connect_to_database():
    return psycopg2.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )

# создаем базу данных sqlite3
# with sqlite3.connect("petrik_audio.db") as db:
#     cursor = db.cursor()
#     query1 = """
#     CREATE TABLE IF NOT EXIsTS content (
#       id Integer PRImARY KEY NOT NULL,
#       title TEXT, descript TEXT,
#       url TEXT,
#       url_preview TEXT,
#       duration TEXT,
#       text TEXT,
#       key_word TEXT,
#       key_channel INTEGER) """
#     cursor.execute(query1)
#
#     db.commit()


# добавление записи в базу
# def add_sql_content(title_a, descript_a, url_a, url_preview_a, duration_a, text_a):
#     with sqlite3.connect("petrik_audio.db") as db:
#         cursor = db.cursor()  # id Integer PRImARY KEY NOT NULL, title TEXT, descript TEXT, url TEXT,url_preview text, duration INTEGER, text TEXT)
#         query = """INSERT INTO content (title, descript, url,url_preview, duration,text) VALUES (?,?,?,?,?,?)"""  # ,video.title
#         data = (title_a, descript_a, url_a, url_preview_a, duration_a, text_a)
#         cursor.execute(query, data)
#         db.commit()
#     return

def add_sql_content(title_a, descript_a, url_a, url_preview_a, duration_a, text_a):
    #подкл к базе
    #conn = connect_to_database()
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    if text_a == 'None':
        text_a = 'нет субтитров'
    try:
        query = """INSERT INTO content_20_04_2024 (title, descript, 
        url,url_preview, duration, post) VALUES (%s, %s, %s, %s, %s, %s)"""  # ,video.title
        data = (title_a, descript_a, url_a, url_preview_a, duration_a, text_a)
        # Выполнение запроса
        cursor.execute(query, data)
        print("Запись успешно добавлена")
        conn.commit()
    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Закрытие соединения
        conn.close()

# Функция перевода длительности видео из PT12M40S в час мин сек
def iso8601_to_minutes_seconds(iso_duration):
    duration = iso_duration[2:]  # Удаление "PT" в начале строки
    hours = minutes = seconds = 0

    if 'H' in duration:
        hours, duration = duration.split('H')
        hours = int(hours)

    if 'M' in duration:
        # Обрабатываем минуты
        if 'H' in duration:
            minutes = duration.split('H')[1].split('M')[0]
        else:
            minutes = duration.split('M')[0]
        minutes = int(minutes)

    if 'S' in duration:
        # Обрабатываем секунды
        if 'M' in duration:
            seconds = duration.split('M')[1].split('S')[0]
        else:
            seconds = duration.split('S')[0]
        seconds = int(seconds)
    if hours == 0:
        hours = "0"
    duration_full = str(hours) + "." + str(minutes) + "." + str(seconds)
    return duration_full  # f"{hours}.{minutes}.{seconds}"


# Пример использования
# iso_duration = "PT12M40S"
# formatted_duration = iso8601_to_minutes_seconds(iso_duration)
# print(formatted_duration)

 # получаем описание видео по ID
def get_video_description(video_id):
    try:
        video_info = youtube.videos().list(part='snippet', id=video_id).execute()
        description = video_info['items'][0]['snippet']['description']
        return description
    except Exception as e:
        print(f"An error occurred while fetching description for video ID {video_id}: {e}")
        return None

# функция возвращает субтитры видео
def get_video_transcripts(video_id):
    try:
        trans = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru', 'en'])
        trans_clear = re.findall(r"[а-яА-Я]+", str(trans))
        # print("Субтитры для видео ID %s:" % video_id)
        # print(trans_clear)

    except Exception as e:  # обработка отсутсвия субтитров
        if "Transcript unavailable" in str(e):  # Проверяем, что исключение вызвано отсутствием субтитров
            print(f"No subtitles available for video ID {video_id}")
            return "нет субтитров"
        else:
            print(f"An error occurred while fetching transcript for video ID {video_id}: {e}")
            return None

    # except Exception as e:
    #        print(f"An error occurred while fetching transcript for video ID {video_id}: {e}")

    # video_ids = ['qUSd99z8Wuk']
    # titr = get_video_transcripts(video_ids)
    return (trans_clear)


#cleaned_text = re.findall(r"[а-яА-Я]+", str(data_db[:3]))


def get_channel_videos(channel_id):
    res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    videos = []
    next_page_token = None
    n_video = 1  # счетчик видео
    # print(json.dumps(res, sort_keys=True, indent=4))

    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, part='snippet', maxResults=50,
                                           pageToken=next_page_token).execute()
        videos.extend(res['items'])
        next_page_token = res.get('nextPageToken')

        if next_page_token is None:
            break

    for video in videos:
        # print("Video Title: %s\nVideo ID: %s\n" % (video['snippet']['title'], video['snippet']['resourceId']['videoId']))
        # video.['']
        video_id = video['snippet']['resourceId']['videoId']

        # Убрать видео по  ID
        # if video_id in ['fut7NL7_Fm0','HRCyi6bL3EA','CsBYndbvp28','zuT6oFc2z44','geh-o5NUma0','9syQK-fsPS4','vztg9I6WVm8','Wy43zn6T4kw','3hF74Klz1Z8','g82Zp-amBh8','uV90U5eocPU']:
        #  continue # пропуск видео на  англ и укр

        video_title = video['snippet']['title']
        video_description = video['snippet']['description']

        # Дополнительный запрос для получения информации о видео
        video_info = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
        video_snippet = video_info['items'][0]['snippet']
        video_content_details = video_info['items'][0]['contentDetails']

        # Извлечение длительности видео
        video_duration = iso8601_to_minutes_seconds(video_content_details['duration'])
        #print(type(video_duration))

        # Получение URL превью видео
        video_thumbnail_url = str(video_snippet['thumbnails']['default']['url'])

        # Получение субтитров
        subtitles = str(get_video_transcripts(video_id))
        print(f'video_id:{video_id}, {video_title}, {video_duration}')
        #print(video_description) #Описание видео
        # print(f'превью URL: {video_thumbnail_url}')
        #print(f'video_id:{video_id}')

        # Добавление инфы о видео в базу таблица content
        # add_sql_content(title_a, descript_a, url_a, url_preview_a, duration_a, text_a)
        add_sql_content(video_title, video_description, video_id, video_thumbnail_url, video_duration, subtitles)

        print(n_video)
        n_video += 1
        if n_video > 1000:
            break
    print(f'Всего на канале {n_video} видео')


if __name__ == '__main__':
    try:
        get_channel_videos("UCmyE72X4HsC7XD-z6QIQpzw")  # ID канала petrik UC8k2L8NWKFOk6eFMUUpoCEw
        # ID Доктор Евдокименко "UCmyE72X4HsC7XD-z6QIQpzw"
        # ID ищем в показать код на главной странице  канал Ищем Ctrl+f ChannelId
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')

