from vkbottle.bot import Message


def requires_correct_menu(menu: str):
    def decorator(func):
        async def wrapper(self, message: Message):
            user_id = message.from_id
            if await self.is_correct_menu(user_id, menu):
                return await func(self, message)
        return wrapper
    return decorator