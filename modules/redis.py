from logging import getLogger

from redis.asyncio import Redis

from modules import Module
from modules.config import ConfigModule

LOGGER = getLogger("RedisModule")


class RedisModule(Module):
    redis: Redis
    required_dependencies = [ConfigModule]

    async def on_load(self, *args, **kwargs) -> None:
        config: ConfigModule = self.dependencies[ConfigModule]

        host = config.data.REDIS_HOST
        port = config.data.REDIS_PORT
        database = config.data.REDIS_DATABASE
        password = config.data.REDIS_PASSWORD

        self.redis = Redis(host=host, port=port, password=password, db=database)
        LOGGER.info("Successfully connected to the Redis!")

    async def on_unload(self) -> None:
        await self.redis.aclose()
        LOGGER.info("Redis connection was successfully closed.")

    async def set_menu(self, user_id: int, menu: str) -> None:  # TODO: menu должен иметь свой отдельный enum, чтобы типы были безопаснее
        await self.redis.set(f"menu:{user_id}", menu)

    async def get_menu(self, user_id: int) -> str:
        try:
            return (await self.redis.get(f"menu:{user_id}")).decode("utf-8")
        except AttributeError:
            await self.set_menu(user_id, "")  # TODO: решить, нужен ли этот вызов здесь
            return ""

