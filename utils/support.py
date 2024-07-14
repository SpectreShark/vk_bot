# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
# from vkbottle import Keyboard, KeyboardButtonColor, Text, Bot
# from vkbottle.bot import Message
#
# from models.support import Support
# from modules.bot import VkBotModule
#
# async def sent_request_to_support(connection: async_sessionmaker[AsyncSession], bot: Bot, message: Message):
#     user_id = message.from_id
#     user_info = await VkBotModule.bot.api.users.get(user_ids=user_id, fields=['first_name', 'last_name'])
#     full_name = f"{user_info[0].first_name} {user_info[0].last_name}"
#
#     keyboard = (
#         Keyboard(inline=True)
#         .add(Text('Перейти к диалогу',
#         payload={"type": "open_link", "link": f"https://vk.com/gim220612553?sel={user_id}"}),
#         color=KeyboardButtonColor.POSITIVE)
#     ).get_json()
#     async with connection() as session:
#         result = (await session.execute(select(Support))).fetchall()[0]
#         for specialist_id in result:
#             print(specialist_id)
