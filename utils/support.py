from random import randint
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from vkbottle import Keyboard, KeyboardButtonColor, Text, Bot, OpenLink
from vkbottle.bot import Message

from models.support import Support

async def sent_request_to_support(connection: async_sessionmaker[AsyncSession], bot: Bot, message: Message):
    user_id = message.from_id
    user_info = await bot.api.users.get(user_ids=user_id, fields=['first_name', 'last_name'])
    full_name = f"{user_info[0].first_name} {user_info[0].last_name}"

    keyboard = (
        Keyboard(inline=True)
        .add(OpenLink(f"https://vk.com/gim220612553?sel={user_id}", "Перейти в диалог"),
            color=KeyboardButtonColor.POSITIVE)
    ).get_json()
    for el in await get_specialist_ids(connection):
        try:
            await bot.api.messages.send(user_id=el, message=f"Пользователю '{full_name}' требуется специалист.",
                keyboard=keyboard, random_id=randint(1, 1000000))
        except Exception as err:
            print(err)
            continue



async def get_specialist_ids(connection: async_sessionmaker[AsyncSession]) -> List[int]:
    async with connection() as session:
        result = (await session.execute(select(Support))).fetchall()
        return [el.user_id for i in result for el in i]
