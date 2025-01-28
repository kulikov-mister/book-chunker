# loader.py
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram import Bot, Dispatcher
from config_data.config import Config, load_config

config: Config = load_config()

bot = Bot(token=config.tg_bot.token, disable_web_page_preview=False, parse_mode="HTML", protect_content=True)
dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.GLOBAL_USER)