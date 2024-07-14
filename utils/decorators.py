from vkbottle.bot import Message
from functools import wraps

def requires_menu(menu: str | list):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, message: Message):
            user_id = message.from_id
            if isinstance(menu, list):
                if any(await self.is_correct_menu(user_id, el) for el in menu):
                    return await func(self, message)
                else:
                    await self.on_unknown_command(message)
            elif await self.is_correct_menu(user_id, menu):
                return await func(self, message)
            else:
                return await self.on_unknown_command(message)
        return wrapper
    return decorator
