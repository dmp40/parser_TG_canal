import aiocron
import asyncio
import datetime
from video_subtitr_API import check_and_add_new_videos

@aiocron.crontab('*/1 * * * *')
async def hi():
    print(f"Привет Дима! Сейчас {datetime.datetime.now()}")
    #await check_and_add_new_videos("UCY649zJeJVhhJa-rvWThZ2g", "utin")

asyncio.get_event_loop().run_forever()