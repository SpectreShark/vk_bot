from tortoise import Tortoise

from modules import Module
from modules.config import ConfigModule

from logging import getLogger

LOGGER = getLogger("DatabaseModule")


class DatabaseModule(Module):
    required_dependencies = [ConfigModule]

    async def on_load(self, *args, **kwargs) -> None:
        config: ConfigModule = self.dependencies[ConfigModule]

        host = config.data.POSTGRES_HOST
        port = config.data.POSTGRES_PORT
        username = config.data.POSTGRES_USER
        database = config.data.POSTGRES_DATABASE
        password = config.data.POSTGRES_PASSWORD

        await Tortoise.init(
            modules={"models": ["models"]},
            db_url=f"asyncpg://{username}:{password}@{host}:{port}/{database}",
        )
        LOGGER.info("Successfully connected to the database!")

        await Tortoise.generate_schemas()
        LOGGER.info("Tortoise schemas was successfully generated.")

    async def on_unload(self) -> None:
        await Tortoise.close_connections()
        LOGGER.info("Database connection was successfully closed.")
