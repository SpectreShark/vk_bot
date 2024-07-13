from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models import BaseModel
from modules import Module
from modules.config import ConfigModule

from logging import getLogger

LOGGER = getLogger("DatabaseModule")


class DatabaseModule(Module):
    required_dependencies = [ConfigModule]

    session: async_sessionmaker[AsyncSession]

    async def on_load(self, *args, **kwargs) -> None:
        config: ConfigModule = self.dependencies[ConfigModule]

        host = config.data.POSTGRES_HOST
        port = config.data.POSTGRES_PORT
        username = config.data.POSTGRES_USER
        database = config.data.POSTGRES_DATABASE
        password = config.data.POSTGRES_PASSWORD

        engine = create_async_engine(f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}")
        self.session = async_sessionmaker(engine, expire_on_commit=False)
        LOGGER.info("Successfully connected to the database!")
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

        LOGGER.info("Database schemas was successfully generated.")
