from os import environ
from modules import Module


class ConfigData:
    REDIS_PASSWORD: str
    REDIS_PORT: int = 6379
    REDIS_DATABASE: int = 0
    REDIS_HOST: str = "redis"

    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_DATABASE: str = "postgres"

    VK_GROUP_ID: int
    VK_BOT_TOKEN: str


class ConfigModule(Module):
    data = ConfigData()

    async def on_load(self) -> None:
        for field in ConfigData.__annotations__:
            value = None
            try:
                value = self.data.__getattribute__(field)
            except AttributeError:
                pass

            # TODO: extract type and convert into it
            self.data.__setattr__(field, environ.get(field, value))
