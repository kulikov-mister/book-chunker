# loader.py
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config_data.config import Config, load_config


config: Config = load_config()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.GLOBAL_USER)
