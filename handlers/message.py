from collections import defaultdict
from typing import List

from sqlalchemy.dialects.postgresql import array
from sqlalchemy import select, insert, update, func, delete
from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message

import keyboards
from models import Item, Support
from modules import DEPENDENCIES_TYPE
from modules.redis import RedisModule
from modules.database import DatabaseModule
from utils import requires_menu
from utils.decorators import requires_admin_menu
from utils.support import sent_request_to_support, get_specialist_ids


class MessageHandler:
    def __init__(self, dependencies: DEPENDENCIES_TYPE, bot: Bot) -> None:
        self.dependencies = dependencies
        self.redis: RedisModule = self.dependencies[RedisModule]
        self.database: DatabaseModule = self.dependencies[DatabaseModule]
        self.bot: Bot = bot

    async def is_correct_menu(self, user_id: int, menu: str) -> bool:
        return await self.redis.get_menu(user_id) == menu

    async def is_correct_admin_menu(self, user_id: int, menu: str) -> bool:
        return '_'.join((await self.redis.get_menu(user_id)).split('_')[:-1]) == menu

    async def on_unknown_command(self, message: Message) -> None:
        state = await self.redis.get_menu(message.from_id)
        match state:
            case "tech_support":
                return
            case "admin_cancel_rental":
                await self.admin_choice_cancel_rental(message)
                return
        is_message_lease = await self.get_all_lease_menu()
        if message.text in is_message_lease:
            match state:
                case "select_lease":
                    await self.add_lease(message)
                    return
                case "cancel_my_lease":
                    await self.delete_my_lease(message)
                    return
            if "_".join(state.split("_")[:-1]) == "admin_choice_cancel_rental":
                await self.admin_delete_rental(message)
                return
        await message.answer(
            "Указанная вами команда не найдена. Используйте клавиатуру ниже, чтобы вернуться в меню.",
            keyboard=keyboards.unknown_keyboard
        )
        await self.redis.set_menu(message.from_id, "unknown")

    async def on_start_command(self, message: Message) -> None:
        spec_id = await get_specialist_ids(self.database.session)
        if message.from_id in spec_id:
            await message.answer("Главное меню", keyboard=keyboards.admin_start_keyboard)
            await self.redis.set_menu(message.from_id, "admin_start")
        else:
            await message.answer("Главное меню", keyboard=keyboards.start_keyboard)
            await self.redis.set_menu(message.from_id, "start")

    @requires_menu("admin_start")
    async def admin_menu(self, message: Message) -> None:
        await message.answer("Админская панель", keyboard=keyboards.admin_menu_keyboard)
        await self.redis.set_menu(message.from_id, "admin_menu")

    @requires_menu("admin_menu")
    async def admin_get_all_rentals(self, message: Message) -> None:
        result = await self.get_all_rental_lease()
        text = f"Список всех людей: {result}"
        if result == "":
            text = "Нет людей, которые забронировали аренду"
        await message.answer(text, keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "admin_all_rentals")

    @requires_menu("admin_menu")
    async def admin_cancel_rental(self, message: Message) -> None:
        query = await self.get_all_rental_name()
        if query == []:
            await message.answer("Нет людей, которые забронировали вещи", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "admin_cancel_rental_null")
        else:
            keyboard = (Keyboard(one_time=True, inline=False))
            for ind, name in enumerate(query):
                if (ind + 1) % 2 == 0:
                    keyboard.row()
                keyboard.add(Text(name[1]), color=KeyboardButtonColor.PRIMARY)
            keyboard.row()
            keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
            await message.answer("Выберите человека, которому нужно отменить аренду", keyboard=keyboard)
            await self.redis.set_menu(message.from_id, "admin_cancel_rental")

    @requires_menu("admin_menu")
    async def admin_add_tech_support(self, message: Message) -> None:
        async with self.database.session() as session:
            result = (await session.execute(select(Support))).fetchall()
            list_menu = [el.user_id for user in result for el in user]
            if not (message.text).isdigit():
                message.answer("Введите уникальный индификатор человека, которого хотите добавить. Для получение"
                               " индификатора человека, ему нужно написать 'Получить id'.", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")
            if message.text in list_menu:
                message.answer("Человек уже является тех. специалистом", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")
            else:
                (await session.execute(insert(Support).values(message.text)))
                (await session.commit())
                message.answer("Человек добавлен в тех. специалисты", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")

    @requires_menu("admin_menu")
    async def admin_delete_tech_support(self, message: Message) -> None:
        async with self.database.session() as session:
            result = (await session.execute(select(Support))).fetchall()
            list_menu = [el.user_id for user in result for el in user]
            if not (message.text).isdigit():
                message.answer("Введите уникальный индификатор человека, которого хотите удалить. Для получение"
                               " индификатора человека, ему нужно написать 'Получить id'.",
                               keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_delete_tech_support")
            if message.text in list_menu:
                message.answer("Человек не является тех. специалистом", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_delete_tech_support")
            else:
                (await session.execute(delete(Support).filter(Support.user_id == message.text)))
                (await session.commit())
                message.answer("Человек удален из тех. специалистов", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_delete_tech_support")


    @requires_menu("admin_cancel_rental")
    async def admin_choice_cancel_rental(self, message: Message) -> None:
        query = await self.get_all_rental_name()
        user_id = ([el[0] for el in query if el[1] == message.text])
        if user_id == []:
            await message.answer("Данный человек не бронировал аренду", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "admin_choice_cancel_rental_null")
        else:
            keyboard = (Keyboard(one_time=True, inline=False))
            list_lease = await self.get_list_rentals(user_id)
            for ind, el in enumerate(list_lease):
                if (ind + 1) % 2 == 0:
                    keyboard.row()
                keyboard.add(Text(el), color=KeyboardButtonColor.PRIMARY)
            keyboard.row()
            keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
            await message.answer("Выберите какую аренду Вы хотите отменить человеку", keyboard=keyboard)
            await self.redis.set_menu(message.from_id, f"admin_choice_cancel_rental_{user_id}")

    @requires_admin_menu("admin_choice_cancel_rental")
    async def admin_delete_rental(self, message: Message) -> None:
        user_id = int(((await self.redis.get_menu(message.from_id)).split('_')[-1]).replace('[', '').replace(']', ''))
        query = await self.get_my_cancel_lease(user_id)
        if message.text in query:
            async with self.database.session() as session:
                result = await session.execute(select(Item).filter(Item.name == message.text))
                item = result.scalars().first()
                if user_id in item.renters_users_id:
                    updated_renters_users_id = item.renters_users_id.copy()
                    updated_renters_users_id.remove(user_id)

                    await session.execute(
                        update(Item)
                        .filter(Item.name == message.text)
                        .values(
                            renters_users_id=updated_renters_users_id,
                            quantity_on_sunday=item.quantity_on_sunday + 1
                        )
                    )

                    await session.commit()
                    await message.answer(f"Вы успешно отменили бронирование {message.text}",
                                         keyboard=keyboards.back_keyboard)
                    await self.redis.set_menu(message.from_id, "admin_delete_rental")
        else:
            await message.answer("У человека не забронирована данная вещь")
            await self.redis.set_menu(message.from_id, "admin_delete_rental")

    @requires_menu(["start", "admin_start"])
    async def information(self, message: Message) -> None:
        await message.answer("Меню информации", keyboard=keyboards.information_keyboard)
        await self.redis.set_menu(message.from_id, "info")

    @requires_menu("info")
    async def choice_polygon(self, message: Message) -> None:
        await message.answer("Выберите один из полигонов", keyboard=keyboards.choice_polygon_keyboard)
        await self.redis.set_menu(message.from_id, "choice_polygon")

    @requires_menu(["start", "admin_start"])
    async def lease(self, message: Message) -> None:
        await message.answer("Меню аренды", keyboard=keyboards.lease_keyboard)
        await self.redis.set_menu(message.from_id, "lease_menu")

    @requires_menu("lease_menu")
    async def select_lease(self, message: Message) -> None:
        text = "Выберите аренду"
        select_lease_keyboard = (Keyboard(one_time=True, inline=False))
        lease_list = await self.get_lease()
        for ind, el in enumerate(lease_list):
            if (ind + 1) % 2 == 0:
                select_lease_keyboard.row()
            select_lease_keyboard.add(Text(el), color=KeyboardButtonColor.PRIMARY)
        if lease_list != []:
            select_lease_keyboard.row()
        else:
            text = "Аренда закончилась"
        select_lease_keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)

        await message.answer(text, keyboard=select_lease_keyboard)

        await self.redis.set_menu(message.from_id, "select_lease")

    @requires_menu("select_lease")
    async def add_lease(self, message: Message) -> None:
        query = await self.get_lease()
        if message.text in query:
            user_id = message.from_id
            async with self.database.session() as session:
                result = await session.execute(select(Item).filter(Item.name == message.text))
                item = result.scalars().first()
                updated_renters_users_id = (item.renters_users_id or []).copy()
                updated_renters_users_id.append(user_id)

                await session.execute(
                    update(Item)
                    .filter(Item.name == message.text)
                    .values(
                        renters_users_id=updated_renters_users_id,
                        quantity_on_sunday=item.quantity_on_sunday - 1
                    )
                )

                await session.commit()
                await message.answer(f"Вы успешно забронировали {message.text}", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "add_lease")
        else:
            await message.answer("Данный тип аренды закончился.", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "add_lease")


    @requires_menu("lease_menu")
    async def price_lease(self, message: Message) -> None:
        await message.answer(f"Список цен:\n{await self.get_price_lease()}", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "price_lease")

    @requires_menu("lease_menu")
    async def remaining_lease(self, message: Message) -> None:
        remaining_string = await self.get_remaining_lease()
        if remaining_string == "":
            remaining_string = 'Все вещи заняты'
        await message.answer(f"Список оставшихся вещей:\n{remaining_string}", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "remaining_lease")

    @requires_menu("lease_menu")
    async def my_lease(self, message: Message) -> None:
        remaining_string = await self.get_my_lease(message.from_id)
        text = f"Список Ваших арендованных вещей:\n{remaining_string}"
        if remaining_string == "":
            text = "Вы не бронировали вещи!"
        await message.answer(text, keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "my_lease")

    @requires_menu("lease_menu")
    async def cancel_my_lease(self, message: Message) -> None:
        remaining_string = (await self.get_my_cancel_lease(message.from_id))
        text = "Выберите, какой тип аренды Вы хотите отменить"
        if remaining_string == []:
            text = "Вы не бронировали вещи!"
            cancel_keyboards = keyboards.back_keyboard
        else:
            cancel_keyboards = (Keyboard(one_time=True, inline=False))
            for ind, el in enumerate(remaining_string):
                if (ind + 1) % 2 == 0:
                    cancel_keyboards = cancel_keyboards.row()
                cancel_keyboards.add(Text(el), color=KeyboardButtonColor.PRIMARY)
            cancel_keyboards.row()
            cancel_keyboards.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
        await message.answer(text, keyboard=cancel_keyboards)
        await self.redis.set_menu(message.from_id, "cancel_my_lease")

    @requires_menu("cancel_my_lease")
    async def delete_my_lease(self, message: Message) -> None:
        user_id = message.from_id
        query = await self.get_my_cancel_lease(user_id)
        if message.text in query:
            async with self.database.session() as session:
                result = await session.execute(select(Item).filter(Item.name == message.text))
                item = result.scalars().first()
                if user_id in item.renters_users_id:
                    updated_renters_users_id = item.renters_users_id.copy()
                    updated_renters_users_id.remove(user_id)

                    await session.execute(
                        update(Item)
                        .filter(Item.name == message.text)
                        .values(
                            renters_users_id=updated_renters_users_id,
                            quantity_on_sunday=item.quantity_on_sunday + 1
                        )
                    )

                    await session.commit()
                    await message.answer(f"Вы успешно отменили бронирование {message.text}", keyboard=keyboards.back_keyboard)
                    await self.redis.set_menu(message.from_id, "delete_lease")
        else:
            await message.answer("Вы не бронировали данный тип аренды!", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "delete_lease")

    @requires_menu(["start", "admin_start"])
    async def help_menu(self, message: Message) -> None:
        await message.answer("Меню помощи", keyboard=keyboards.help_menu_keyboard)
        await self.redis.set_menu(message.from_id, "help_menu")

    @requires_menu("help_menu")
    async def technical_support(self, message: Message) -> None:
        await message.answer("В скором времени с Вами свяжется специалист.", keyboard=keyboards.tech_support_keyboard)
        await sent_request_to_support(self.database.session, self.bot, message)
        await self.redis.set_menu(message.from_id, "tech_support")

    @requires_menu("help_menu")
    async def frequently_asked_questions(self, message: Message) -> None:
        await message.answer("Часто задаваемые вопросы", keyboard=keyboards.question_frequent)
        await self.redis.set_menu(message.from_id, "question_frequent")

    async def get_id(self, message: Message) -> None:
        await message.answer(f"Ваш id - {message.from_id}", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "get_id")

    async def on_back(self, message: Message) -> None:
        menu = await self.redis.get_menu(message.from_id)
        state = "_".join((await self.redis.get_menu(message.from_id)).split("_")[:-1])
        match menu:
            case "info" | "lease_menu" | "help_menu" | "tech_support" | "admin_menu" | "get_id":
                await self.on_start_command(message)
            case "admin_all_rentals" | "admin_cancel_rental_null" | "admin_cancel_rental":
                await self.admin_menu.__wrapped__(self, message)
            case "admin_choice_cancel_rental_null" | "admin_delete_rental":
                await self.admin_cancel_rental.__wrapped__(self, message)
            case "choice_polygon":
                await self.information.__wrapped__(self, message)
            case "question_frequent":
                await self.help_menu.__wrapped__(self, message)
            case "cancel_my_lease" | "my_lease" | "remaining_lease" | "price_lease" | "select_lease" | "add_lease":
                await self.lease.__wrapped__(self, message)
            case "delete_lease":
                if (await self.get_my_cancel_lease(message.from_id)) == []:
                    await self.lease.__wrapped__(self, message)
                else:
                    await self.cancel_my_lease.__wrapped__(self, message)
            case _:
                if state == "admin_choice_cancel_rental":
                    await self.admin_cancel_rental.__wrapped__(self, message)
                else:
                    await self.on_unknown_command(message)

    async def get_lease(self) -> list:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.quantity_on_sunday > 0).order_by(Item.name))).fetchall()
            name = [el.name for item in result for el in item]
            return name

    async def get_all_lease_menu(self) -> list:
        async with self.database.session() as session:
            result = (await session.execute(select(Item))).fetchall()
            list_menu = [el.name for item in result for el in item]
            return list_menu

    async def get_remaining_lease(self) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).order_by(Item.name))).fetchall()
            name_quantity = [f"\n{el.name} - {el.quantity_on_sunday} шт.\n" for i in result for el in i]
            return "".join(name_quantity)

    async def get_price_lease(self) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).order_by(Item.name))).fetchall()
            name_price = [f"\n{el.name} - {el.price} руб.\n" for i in result for el in i]
            return "".join(name_price)

    async def get_my_lease(self, user_id: int) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.renters_users_id.contains([user_id])))).fetchall()
            item_counts = defaultdict(int)
            for i in result:
                for el in i:
                    item_counts[el.name] += el.renters_users_id.count(user_id)
            return "".join([f"\n{name} - {count} шт." for name, count in item_counts.items()])

    async def get_my_cancel_lease(self, user_id) -> list:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.renters_users_id.contains([user_id])))).fetchall()
            return [el.name for i in result for el in i]

    async def get_all_rental_lease(self) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(func.cardinality(Item.renters_users_id) > 0))).fetchall()
            item_counts = defaultdict(lambda: defaultdict(int))
            for row in result:
                item = row[0]
                for user_id in item.renters_users_id:
                    user_info = await self.bot.api.users.get(user_ids=user_id, fields=['first_name', 'last_name'])
                    if user_info:
                        full_name = f"{user_info[0].first_name} {user_info[0].last_name}"
                        item_counts[full_name][item.name] += 1
            all_users_lease = []
            for full_name, items in item_counts.items():
                for name, count in items.items():
                    all_users_lease.append(f"\n{full_name} - {name} - {count} шт.\n")
            return "".join(all_users_lease)

    async def get_all_rental_name(self) -> list[list[str]]:
        async with self.database.session() as session:
            list_name = []
            try:
                result = (await session.execute(select(Item).filter(func.cardinality(Item.renters_users_id) > 0))).fetchall()[0]
            except IndexError:
                result = []
            for el in result:
                if any([el[1] == i for i in list_name]):
                    continue
                user_info = await self.bot.api.users.get(user_ids=el.renters_users_id, fields=['first_name', 'last_name'])
                full_name = f"{user_info[0].first_name} {user_info[0].last_name}"
                list_name.append([el.renters_users_id, full_name])
            return list_name

    async def get_list_rentals(self, user_id) -> list[str]:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.renters_users_id.contains([user_id])))).fetchall()
            return [el.name for item in result for el in item]