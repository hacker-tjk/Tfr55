import asyncio
import logging
from bot import create_bot
import handlers

async def main():
    # Встроенная настройка логов вместо внешнего файла
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    bot, dp = create_bot()
    
    # Регистрация всех функций из файла handlers
    handlers.register_handlers(dp)
    
    print("AI 🧠 IMAGE HD запущен и готов к работе!")
    
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
