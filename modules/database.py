from modules import Module
from modules.config import ConfigModule

from logging import getLogger

from models import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine

LOGGER = getLogger("DatabaseModule")


class DatabaseModule(Module):
    required_dependencies = [ConfigModule]

    engine: AsyncEngine
    session: async_sessionmaker[AsyncSession]

    async def on_load(self, *args, **kwargs) -> None:
        config: ConfigModule = self.dependencies[ConfigModule]

        host = config.data.POSTGRES_HOST
        port = config.data.POSTGRES_PORT
        username = config.data.POSTGRES_USER
        database = config.data.POSTGRES_DATABASE
        password = config.data.POSTGRES_PASSWORD

        self.engine = create_async_engine(f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}", echo=True)
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)
        LOGGER.info("Successfully connected to the database!")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        LOGGER.info("Database schemas was successfully generated.")

    async def on_unload(self) -> None:
        await self.engine.dispose()
