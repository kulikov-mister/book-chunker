import asyncio
import logging

from loader import dp, bot
from keyboards.main_menu import set_main_menu
import handlers


# Инициализируем логгер
logger = logging.getLogger(__name__)

# Конфигурируем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
            '[%(asctime)s] - %(name)s - %(message)s')

# Функция конфигурирования и запуска бота
async def main():
    await set_main_menu(bot)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())



