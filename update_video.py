import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import psycopg2
from  video_subtitr_API  import iso8601_to_minutes_seconds, get_video_transcripts, add_sql_content

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

def create_video_ids_table():
    """Создает таблицу для хранения ID видео, если она не существует."""
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS video_ids (
        video_id VARCHAR PRIMARY KEY,
        added_date TIMESTAMP
    )
    """
    cursor.execute(query)
    conn.commit()
    conn.close()

def is_video_id_in_db(video_id):
    """Проверяет, есть ли видео ID в базе данных."""
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    query = "SELECT 1 FROM video_ids WHERE video_id = %s"
    cursor.execute(query, (video_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_video_id_to_db(video_id):
    """Добавляет видео ID в базу данных."""
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    query = "INSERT INTO video_ids (video_id, added_date) VALUES (%s, %s)"
    cursor.execute(query, (video_id, datetime.datetime.now()))
    conn.commit()
    conn.close()

def check_and_add_new_videos(channel_id):
    """Проверяет наличие новых видео на канале и добавляет их данные в базу."""
    res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    videos = []
    next_page_token = None

    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, part='snippet', maxResults=50,
                                           pageToken=next_page_token).execute()
        videos.extend(res['items'])
        next_page_token = res.get('nextPageToken')
        if next_page_token is None:
            break

    new_videos_count = 0
    for video in videos:
        video_id = video['snippet']['resourceId']['videoId']
        if not is_video_id_in_db(video_id):
            video_title = video['snippet']['title']
            video_description = video['snippet']['description']

            video_info = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
            video_snippet = video_info['items'][0]['snippet']
            video_content_details = video_info['items'][0]['contentDetails']

            video_duration = iso8601_to_minutes_seconds(video_content_details['duration'])
            video_thumbnail_url = str(video_snippet['thumbnails']['default']['url'])
            subtitles = str(get_video_transcripts(video_id))

            add_sql_content(video_title, video_description, video_id, video_thumbnail_url, video_duration, subtitles)
            add_video_id_to_db(video_id)
            new_videos_count += 1

    print(f'Добавлено {new_videos_count} новых видео')

if __name__ == '__main__':
    create_video_ids_table()
    try:
        check_and_add_new_videos("UC-7rh_mZOLWcBKMbMFieOGA")
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
