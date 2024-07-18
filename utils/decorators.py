from vkbottle.bot import Message
from functools import wraps


async def async_any(async_iterable):
    async for item in async_iterable:
        if item:
            return True
    return False


def requires_menu(menu: str | list):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, message: Message):
            user_id = message.from_id
            if isinstance(menu, list):
                if await async_any(await self.is_correct_menu(user_id, el) for el in menu):
                    return await func(self, message)
                else:
                    await self.on_unknown_command(message)
            elif await self.is_correct_menu(user_id, menu):
                return await func(self, message)
            else:
                return await self.on_unknown_command(message)

        return wrapper

    return decorator

def requires_admin_menu(menu: str):
    def decorators(func):
        @wraps(func)
        async def wrapped(self, message: Message):
            user_id = message.from_id
            if await self.is_correct_admin_menu(user_id, menu):
                return await func(self, message)
            else:
                return await self.on_unknown_command(message)

        return wrapped

    return decorators