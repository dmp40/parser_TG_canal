import nats
import asyncio
#Функция отправки сообщений NATS
async def on_new_video(video_id, user_id, video_title):
    nc = await nats.connect("nats://localhost:4222")
    message = {
        'video_id': video_id,
        'user_id': user_id,
        'video_title': video_title
    }
    await nc.publish("new_videos", str(message).encode())
    await nc.drain()

if __name__ == '__main__':
    asyncio.run( on_new_video('555658','Упржнения для 90+','Утин канал'))