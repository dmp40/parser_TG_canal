import aiocron
import asyncio
import datetime

# Функция, которая будет вызываться по расписанию
@aiocron.crontab("*/1 * * * *")
async def greet():
    print(f"Привет! Сейчас {datetime.datetime.now()}")

# Запуск асинхронного цикла событий
async def main():
    print("Запуск планировщика")
    greet.start()  # Запуск планировщика
    while True:
        await asyncio.sleep(1)  # Задержка, чтобы цикл продолжался

if __name__ == "__main__":
    print("Запуск основного цикла")
    asyncio.run(main())
