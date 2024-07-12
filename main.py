from asyncio import run
from logging import INFO

from modules import ModuleManager
from modules.bot import VkBotModule
from modules.config import ConfigModule
from modules.database import DatabaseModule
from modules.logging import LoggingModule

manager = ModuleManager()
manager.add_module(LoggingModule, {'level': INFO})

manager.add_module(ConfigModule)
manager.add_module(DatabaseModule)
manager.add_module(VkBotModule)  # TODO: настроить graceful shutdown

if __name__ == '__main__':
    run(manager.load_modules())

    # FIXME: уточнить у Миши, в чём может быть проблема
    # run(manager.unload_modules())  # выкидывает RuntimeError: Event loop is closed

