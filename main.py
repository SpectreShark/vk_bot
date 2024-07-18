from asyncio import run
from logging import INFO

from modules import ModuleManager
from modules.bot import VkBotModule
from modules.config import ConfigModule
from modules.database import DatabaseModule
from modules.logging import LoggingModule
from modules.redis import RedisModule

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from modules.scheduler import SchedulerModule

manager = ModuleManager()
manager.add_module(LoggingModule, {'level': INFO})

manager.add_module(ConfigModule)
manager.add_module(DatabaseModule)
manager.add_module(RedisModule)
manager.add_module(SchedulerModule)

manager.add_module(VkBotModule)  # TODO: настроить graceful shutdown


if __name__ == '__main__':
    try:
        run(manager.load_modules())
    finally:
        run(manager.unload_modules())
