from vkbottle.bot import Message

import keyboards
from modules import DEPENDENCIES_TYPE
from modules.redis import RedisModule
from utils.decorator import requires_correct_menu


class MessageHandler:
    def __init__(self, dependencies: DEPENDENCIES_TYPE) -> None:
        self.dependencies = dependencies
        self.redis: RedisModule = self.dependencies[RedisModule]

    async def is_correct_menu(self, user_id: int, menu: str) -> bool:
        return await self.redis.get_menu(user_id) == menu

    async def on_unknown_command(self, message: Message) -> None:
        await message.answer(
            "Указанная вами команда не найдена. Используйте клавиатуру ниже, чтобы вернуться в меню.",
            keyboard=keyboards.unknown_keyboard
        )
        await self.redis.set_menu(message.from_id, "unknown")

    @requires_correct_menu("unknown")
    async def on_start_command(self, message: Message) -> None:
        await message.answer("Главное меню", keyboard=keyboards.start_keyboard)
        await self.redis.set_menu(message.from_id, "start")
        await self.redis.get_menu(message.from_id)

    @requires_correct_menu("info")
    async def information(self, message: Message) -> None:
        await message.answer("Меню информации", keyboard=keyboards.information_keyboard)
        await self.redis.set_menu(message.from_id, "info")

    @requires_correct_menu("choice_polygon")
    async def choice_polygon(self, message: Message) -> None:
        await message.answer("Выберите один из полигонов", keyboard=keyboards.choice_polygon_keyboard)
        await self.redis.set_menu(message.from_id, "choice_polygon")

    @requires_correct_menu("lease_menu")
    async def lease(self, message: Message) -> None:
        await message.answer("Меню аренды", keyboard=keyboards.lease_keyboard)
        await self.redis.set_menu(message.from_id, "lease_menu")

    @requires_correct_menu("select_lease")
    async def select_lease(self, message: Message) -> None:
        await message.answer("Выберите аренду", keyboard=None)  # TODO: add keyboard "give_arends_keyboard"
        await self.redis.set_menu(message.from_id, "select_lease")

    @requires_correct_menu("help_menu")
    async def help_menu(self, message: Message) -> None:
        await message.answer("Меню помощи", keyboard=keyboards.help_menu_keyboard)
        await self.redis.set_menu(message.from_id, "help_menu")

    # TODO: Переделать с несколькими страницами, сделать, чтобы было красиво
    # async def help_questions(self, message: Message) -> None:
    #     keyboard = Keyboard(one_time=True, inline=False)
    #     keyboard.add(Text(), color=KeyboardButtonColor.PRIMARY)
