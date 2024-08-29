from random import randint

import keyboards

from collections import defaultdict

from vkbottle.bot import Message
from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text

from config import question_answer, set_of_kit
from models import Item, Support

from sqlalchemy import select, insert, update, func, delete

from modules import DEPENDENCIES_TYPE
from modules.redis import RedisModule
from modules.database import DatabaseModule

from utils import requires_menu
from utils.decorators import requires_row_menu
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
        is_message_lease = await self.get_all_lease_menu()
        row_state = "_".join(state.split("_")[:-1])
        match state:
            case "tech_support":
                return
            case "admin_add_id_tech_sup":
                await self.admin_add_tech_support(message)
                return

        if message.text in is_message_lease:
            match state:
                case "select_lease":
                    await self.add_lease(message)
                    return
                case "cancel_my_lease":
                    await self.delete_my_lease(message)
                    return

            if row_state == "admin_choice_cancel_rental":
                await self.admin_delete_rental(message)
                return

        if (row_state == "question_frequent") and (message.text not in ["Влево", "Вправо"]):
            if message.text in question_answer:
                await message.answer(question_answer.get(message.text), keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "answer_question_frequent")
                return

        elif (row_state == "admin_delete_id_tech_sup") and (message.text not in ["Вправо", "Влево"]):
            await self.admin_delete_tech_support(message)
            return

        elif (row_state == "admin_cancel_rental") and message.text == "Вправо":
            object = await self.get_all_rental_name()
            await self.next_page(message, 'admin_cancel_rental_list', object)
            return
        elif (row_state == "admin_cancel_rental") and message.text == "Влево":
            await self.back_page(message, 'admin_cancel_rental_list')
            return

        elif (row_state == "admin_cancel_rental") and any(message.text == el[1] for el in \
                                                                                (await self.get_all_rental_name())):
            await self.admin_choice_cancel_rental(message)
            return

        elif (row_state == "admin_delete_id_tech_sup") and message.text == "Вправо":
            object = await self.get_all_support_name_id()
            await self.next_page(message, 'admin_delete_tech_sup', object)
            return
        elif (row_state == "admin_delete_id_tech_sup") and message.text == "Влево":
            await self.back_page(message, 'admin_delete_tech_sup')
            return

        elif (row_state == "question_frequent") and message.text == "Вправо":
            await self.next_page(message, 'list_frequently_asked_questions', question_answer)
            return
        elif (row_state == "question_frequent") and message.text == "Влево":
            await self.back_page(message, 'list_frequently_asked_questions')
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
        await self.redis.set_menu(message.from_id, "admin_cancel_rental_0")
        await self.admin_cancel_rental_list(message)

    @requires_row_menu("admin_cancel_rental")
    async def admin_cancel_rental_list(self, message: Message) -> None:
        query = await self.get_all_rental_name()
        if query == []:
            await message.answer("Нет людей, которые забронировали вещи", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "admin_cancel_rental_null")
        else:
            state = ((await self.redis.get_menu(message.from_id)).split("_"))[-1]
            count = 5 * int(state)
            keyboard = (Keyboard(one_time=True, inline=False))
            names = list(query)[count:count + 5]
            for name in names:
                keyboard.add(Text(name[1]), color=KeyboardButtonColor.PRIMARY)
                keyboard.row()
            keyboard.add(Text("Влево"), color=KeyboardButtonColor.POSITIVE)
            keyboard.add(Text("Вправо"), color=KeyboardButtonColor.POSITIVE)
            keyboard.row()
            keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
            await message.answer("Выберите человека, которому нужно отменить аренду", keyboard=keyboard)

    @requires_menu("admin_menu")
    async def admin_get_all_support(self, message: Message) -> None:
        query: str = await self.get_all_support()
        await message.answer(f"Список всей тех. поддержки:\n {query}", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "admin_get_all_support")

    @requires_menu("admin_menu")
    async def admin_add_id_tech_sup(self, message: Message) -> None:
        await message.answer("Введите уникальный id человека, которого хотите добавить. \
        Для получение id человека, ему нужно написать 'Получить id'.", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "admin_add_id_tech_sup")

    @requires_menu("admin_menu")
    async def admin_delete_id_tech_sup(self, message: Message) -> None:
        await self.redis.set_menu(message.from_id, "admin_delete_id_tech_sup_0")
        await self.admin_delete_tech_sup(message)

    @requires_row_menu("admin_delete_id_tech_sup")
    async def admin_delete_tech_sup(self, message: Message) -> None:
        keyboard = (Keyboard(one_time=True, inline=False))
        list_tech = (await self.get_all_support_name_id())
        state = ((await self.redis.get_menu(message.from_id)).split("_"))[-1]
        count = 5 * int(state)
        names = list(list_tech.keys())[count:count + 5]
        for el in names:
            keyboard.add(Text(el), color=KeyboardButtonColor.PRIMARY)
            keyboard.row()
        keyboard.add(Text("Влево"), color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("Вправо"), color=KeyboardButtonColor.POSITIVE)
        keyboard.row()
        keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
        await message.answer("Выберите человека, которого хотите удалить из тех. специалистов",
                             keyboard=keyboard)

    @requires_menu("admin_add_id_tech_sup")
    async def admin_add_tech_support(self, message: Message) -> None:
        async with self.database.session() as session:
            result = (await session.execute(select(Support))).fetchall()
            list_menu = [el.user_id for user in result for el in user]
            if (not (message.text).isdigit()) and (message.text != "Назад"):
                await message.answer("Введите уникальный id человека, которого хотите добавить. Для получение \
                                     id человека, ему нужно написать 'Получить id'.",
                                     keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")
            elif int(message.text) in list_menu:
                await message.answer("Человек уже является тех. специалистом", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")
            else:
                (await session.execute(insert(Support).values(user_id=int(message.text))))
                (await session.commit())
                await message.answer("Человек добавлен в тех. специалисты", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_add_tech_support")

    @requires_row_menu("admin_delete_id_tech_sup")
    async def admin_delete_tech_support(self, message: Message) -> None:
        async with self.database.session() as session:
            tech_id: int = (await self.get_all_support_name_id()).get(message.text)
            if tech_id is None:
                await message.answer("Человек не является тех. специалистом", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_delete_tech_support")
            else:
                (await session.execute(delete(Support).filter(Support.user_id == tech_id)))
                (await session.commit())
                await message.answer("Человек удален из тех. специалистов", keyboard=keyboards.back_keyboard)
                await self.redis.set_menu(message.from_id, "admin_delete_tech_support")

    @requires_row_menu("admin_cancel_rental")
    async def admin_choice_cancel_rental(self, message: Message) -> None:
        query = await self.get_all_rental_name()
        user_id = ([el[0] for el in query if el[1] == message.text])
        if user_id == []:
            await message.answer("Данный человек не бронировал аренду", keyboard=keyboards.back_keyboard)
            await self.redis.set_menu(message.from_id, "admin_choice_cancel_rental_null")
        else:
            keyboard = (Keyboard(one_time=True, inline=False))
            list_lease = await self.get_my_cancel_lease(user_id)
            for ind, el in enumerate(list_lease):
                if (ind + 1) % 2 == 0:
                    keyboard.row()
                keyboard.add(Text(el), color=KeyboardButtonColor.PRIMARY)
            keyboard.row()
            keyboard.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
            await message.answer("Выберите какую аренду Вы хотите отменить человеку", keyboard=keyboard)
            await self.redis.set_menu(message.from_id, f"admin_choice_cancel_rental_{user_id}")

    @requires_row_menu("admin_choice_cancel_rental")
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
                    if message.text == "Комплект":
                        for el in set_of_kit:
                            await session.execute(
                                update(Item)
                                .filter(Item.name == el)
                                .values(
                                    quantity_on_sunday=item.quantity_on_sunday + 1
                                )
                            )


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
                    await self.bot.api.messages.send(user_id=user_id, message=f"Аренда типа '{message.text}' была отменена администратором. Для больших подробностей обратитесь к администрации через Тех. поддержку", random_id=randint(1, 1000000))
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
        lease_menu = await get_select_lease_menu()
        lease_list = await self.get_lease()
        for ind, el in enumerate(lease_menu):
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
                if message.text == "Комплект":
                    for el in set_of_kit:
                        await session.execute(
                            update(Item)
                            .filter(Item.name == el)
                            .values(
                                quantity_on_sunday=item.quantity_on_sunday - 1
                            )
                        )


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
                    if message.text == "Комплект":
                        for el in set_of_kit:
                            await session.execute(
                                update(Item)
                                .filter(Item.name == el)
                                .values(
                                    quantity_on_sunday=item.quantity_on_sunday + 1
                                )
                            )

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
        await self.redis.set_menu(message.from_id, "question_frequent_0")
        await self.list_frequently_asked_questions(message)

    async def next_page(self, message: Message, function, object) -> None:
        state = ((await self.redis.get_menu(message.from_id)).split("_"))[-1]
        q, r = divmod((len(object) / 5), 1)
        max_count = (round(q) + bool(r)) - 1
        if int(state) != max_count:
            state_row = ((await self.redis.get_menu(message.from_id)).split("_"))
            count = int(state_row[-1])
            state = f'{"_".join(state_row[:-1])}_{count + 1}'
            await self.redis.set_menu(message.from_id, state)
        method = getattr(self, function, None)
        await method(message)


    async def back_page(self, message: Message, function) -> None:
        state = ((await self.redis.get_menu(message.from_id)).split("_"))[-1]
        if int(state) != 0:
            state_row = ((await self.redis.get_menu(message.from_id)).split("_"))
            count = int(state_row[-1])
            state = f'{"_".join(state_row[:-1])}_{count - 1}'
            await self.redis.set_menu(message.from_id, state)
        method = getattr(self, function, None)
        await method(message)

    @requires_row_menu("question_frequent")
    async def list_frequently_asked_questions(self, message: Message) -> None:
        state = ((await self.redis.get_menu(message.from_id)).split("_"))[-1]
        count = 5 * int(state)
        question_frequent = (
            Keyboard(one_time=True, inline=False)
        )
        questions = list(question_answer.keys())[count:count + 5]
        for question in questions:
            question_frequent.add(Text(question), color=KeyboardButtonColor.PRIMARY)
            question_frequent.row()
        question_frequent.add(Text("Влево"), color=KeyboardButtonColor.POSITIVE)
        question_frequent.add(Text("Вправо"), color=KeyboardButtonColor.POSITIVE)
        question_frequent.row()
        question_frequent.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)

        await message.answer("Часто задаваемые вопросы", keyboard=question_frequent)

    async def get_id(self, message: Message) -> None:
        await message.answer(f"Ваш id - {message.from_id}", keyboard=keyboards.back_keyboard)
        await self.redis.set_menu(message.from_id, "get_id")

    async def on_back(self, message: Message) -> None:
        menu = await self.redis.get_menu(message.from_id)
        state = "_".join((await self.redis.get_menu(message.from_id)).split("_")[:-1])
        match menu:
            case "info" | "lease_menu" | "help_menu" | "tech_support" | "admin_menu" | "get_id":
                await self.on_start_command(message)
            case "admin_all_rentals" | "admin_cancel_rental_null" | "admin_add_id_tech_sup" | "admin_get_all_support" | "admin_add_tech_support":
                await self.admin_menu.__wrapped__(self, message)
            case "admin_choice_cancel_rental_null" | "admin_delete_rental":
                await self.admin_cancel_rental.__wrapped__(self, message)
            case "choice_polygon":
                await self.information.__wrapped__(self, message)
            case "cancel_my_lease" | "my_lease" | "remaining_lease" | "price_lease" | "select_lease" | "add_lease":
                await self.lease.__wrapped__(self, message)
            case "admin_delete_tech_support":
                await self.admin_delete_id_tech_sup.__wrapped__(self, message)
            case "answer_question_frequent":
                await self.frequently_asked_questions.__wrapped__(self, message)
            case "delete_lease":
                if (await self.get_my_cancel_lease(message.from_id)) == []:
                    await self.lease.__wrapped__(self, message)
                else:
                    await self.cancel_my_lease.__wrapped__(self, message)
            case _:
                if state == "question_frequent":
                    await self.help_menu.__wrapped__(self, message)
                elif state in ["admin_cancel_rental", "admin_delete_id_tech_sup"]:
                    await self.admin_menu.__wrapped__(self, message)
                elif state == "admin_choice_cancel_rental":
                    await self.admin_cancel_rental.__wrapped__(self, message)
                else:
                    await self.on_unknown_command(message)
# TODO: получение списка для выбора аренды ( выбирает все поля, даже == 0 )
    async def get_select_lease_menu(self) -> list:
        async with self.database.session() as session:
            result = (
                await session.execute(select(Item).order_by(Item.name))).fetchall()
            name = [el.name for item in result for el in item]
            return name
# TODO: получение списка для добавления/удаления аренды ( выбирает все поля в БД, где кол-во > 0 )
    async def get_lease(self) -> list:
        async with self.database.session() as session:
            result = (
                await session.execute(select(Item).filter(Item.quantity_on_sunday > 0).order_by(Item.name))).fetchall()
            name = [el.name for item in result for el in item]
            return name
# TODO: получение списка для проверки, что сообщения содержит название аренды ( берет все значения )
    async def get_all_lease_menu(self) -> list:
        async with self.database.session() as session:
            result = (await session.execute(select(Item))).fetchall()
            list_menu = [el.name for item in result for el in item]
            return list_menu
# TODO: получение всей аренды ( даже той, которой кол-во == 0 ), для списка оставшихся вещей
    async def get_remaining_lease(self) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).order_by(Item.name))).fetchall()
            name_quantity = [f"\n{el.name} - {el.quantity_on_sunday} шт.\n" for i in result for el in i]
            return "".join(name_quantity)
# TODO: получение аренды - цены, для списка цен на аренду
    async def get_price_lease(self) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).order_by(Item.name))).fetchall()
            name_price = [f"\n{el.name} - {el.price} руб.\n" for i in result for el in i]
            return "".join(name_price)
# TODO: получение своей забронированной аренды по user_id ( аренда - кол-во )
    async def get_my_lease(self, user_id: int) -> str:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.renters_users_id.contains([user_id])))).fetchall()
            item_counts = defaultdict(int)
            for i in result:
                for el in i:
                    item_counts[el.name] += el.renters_users_id.count(user_id)
            return "".join([f"\n{name} - {count} шт." for name, count in item_counts.items()])
# TODO: получение всей аренды, которую забронировал человек
    async def get_my_cancel_lease(self, user_id) -> list:
        async with self.database.session() as session:
            result = (await session.execute(select(Item).filter(Item.renters_users_id.contains([user_id])))).fetchall()
            return [el.name for item in result for el in item]
# TODO: получение всех людей, которые забронировали аренду и кол-во аренды, которую они взяли
    async def get_all_rental_lease(self) -> str:
        async with self.database.session() as session:
            result = (
                await session.execute(select(Item).filter(func.cardinality(Item.renters_users_id) > 0))).fetchall()
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

# TODO: CHECK
    async def get_all_rental_name(self) -> list[list[str]]:
        async with self.database.session() as session:
            list_name = []
            try:
                result = \
                    (await session.execute(
                        select(Item).filter(func.cardinality(Item.renters_users_id) > 0))).fetchall()[0]
            except IndexError:
                result = []
            for i in result:
                for el in i.renters_users_id:
                    if any([el == i[0] for i in list_name]):
                        continue
                    user_info = await self.bot.api.users.get(user_ids=el,
                                                             fields=['first_name', 'last_name'])
                    full_name = f"{user_info[0].first_name} {user_info[0].last_name}"
                    list_name.append([el, full_name])
            return list_name
# TODO: получение всей тех. поддержки, для администрации
    async def get_all_support(self) -> str:
        async with self.database.session() as session:
            query = (await session.execute(select(Support))).fetchall()
            list_name = []
            for el in [el.user_id for i in query for el in i]:
                user_info = await self.bot.api.users.get(user_ids=el, fields=['first_name', 'last_name'])
                list_name.append(f"{user_info[0].first_name} {user_info[0].last_name}")
            return "".join([f"{el}\n" for el in list_name])
# TODO: получение имени и индификатора саппорта
    async def get_all_support_name_id(self) -> dict[str, int]:
        async with self.database.session() as session:
            query = (await session.execute(select(Support))).fetchall()
            list_name_id = {}
            list_id = [el.user_id for i in query for el in i]
            for el in list_id:
                user_info = await self.bot.api.users.get(user_ids=el, fields=['first_name', 'last_name'])
                name = f"{user_info[0].first_name} {user_info[0].last_name}"
                list_name_id[name] = int(el)
            return list_name_id
