from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, delete, update
from vkbottle import Bot, API
from logging import getLogger

from handlers import MessageHandler
from models import Item, Support
from modules import Module
from modules.config import ConfigModule
from modules.database import DatabaseModule
from modules.redis import RedisModule

LOGGER = getLogger("BotModule")


class VkBotModule(Module):
    delete_scheduler: AsyncIOScheduler
    bot: Bot = Bot()
    required_dependencies = [ConfigModule, DatabaseModule, RedisModule]

    async def on_load(self) -> None:
        LOGGER.info("Starting up the bot...")
        self.bot.api = API(self.dependencies[ConfigModule].data.VK_BOT_TOKEN)
        message_handler = MessageHandler(self.dependencies, self.bot)

        self.delete_scheduler = AsyncIOScheduler()

        self.delete_scheduler.add_job(self.start_delete_deleted_user, "interval", minutes=10)
        self.delete_scheduler.start()

        self.bot.on.message(text=["Начать", "В главное меню"])(message_handler.on_start_command)

        self.bot.on.message(text="Панель администратора")(message_handler.admin_menu)
        self.bot.on.message(text="Список всей аренды")(message_handler.admin_get_all_rentals)
        self.bot.on.message(text="Отменить аренду человеку")(message_handler.admin_cancel_rental)
        self.bot.on.message(text="Список тех. специалистов")(message_handler.admin_get_all_support)
        self.bot.on.message(text="Добавить тех. специалиста")(message_handler.admin_add_id_tech_sup)
        self.bot.on.message(text="Удалить тех. специалиста")(message_handler.admin_delete_id_tech_sup)

        self.bot.on.message(text="Информация")(message_handler.information)
        self.bot.on.message(text="Как добраться?")(message_handler.choice_polygon)

        self.bot.on.message(text="Аренда")(message_handler.lease)
        self.bot.on.message(text="Аренда вещей")(message_handler.select_lease)
        self.bot.on.message(text="Цены на аренду")(message_handler.price_lease)
        self.bot.on.message(text="Количество оставшейся аренды")(message_handler.remaining_lease)
        self.bot.on.message(text="Мои арендованные вещи")(message_handler.my_lease)
        self.bot.on.message(text="Отменить аренду")(message_handler.cancel_my_lease)

        self.bot.on.message(text="Помощь")(message_handler.help_menu)
        self.bot.on.message(text="Техническая поддержка")(message_handler.technical_support)
        self.bot.on.message(text="Вопрос решен")(message_handler.on_back)
        self.bot.on.message(text="Частые вопросы")(message_handler.frequently_asked_questions)

        self.bot.on.message(text="Получить id")(message_handler.get_id)

        self.bot.on.message(text="Назад")(message_handler.on_back)

        self.bot.on.message()(message_handler.on_unknown_command)

        await self.bot.run_polling()

    async def start_delete_deleted_user(self) -> None:
        user_id_item = await self.get_deleted_user_ids_from_lease()
        user_id_support = await self.get_deleted_user_ids_from_support()
        async with self.dependencies[DatabaseModule].session() as session:
            for tech_id in user_id_support:
                (await session.execute(delete(Support).filter(Support.user_id == tech_id)))
            for user in user_id_item:
                user_id, item_name = user[0], user[1]
                result = await session.execute(select(Item).filter(Item.name == item_name))
                item = result.scalars().first()
                if user_id in item.renters_users_id:
                    updated_renters_users_id = item.renters_users_id.copy()
                    updated_renters_users_id.remove(user_id)

                    await session.execute(
                        update(Item)
                        .filter(Item.name == item_name)
                        .values(
                            renters_users_id=updated_renters_users_id,
                            quantity_on_sunday=item.quantity_on_sunday + 1
                        )
                    )

            await session.commit()

    async def get_deleted_user_ids_from_support(self) -> list:
        deleted_user_ids = []
        async with self.dependencies[DatabaseModule].session() as session:
            query = (await session.execute(select(Support.user_id)))
            all_user_ids = [user_id for el in query for user_id in el]
            for user_id in all_user_ids:
                user_info = await self.bot.api.users.get(user_ids=user_id, fields=['first_name', 'last_name'])
                name = f"{user_info[0].first_name} {user_info[0].last_name}"
                if name == "DELETED ":
                    deleted_user_ids.append(user_id)

        return deleted_user_ids

    async def get_deleted_user_ids_from_lease(self) -> list:
        deleted_users_ids: list = []
        async with self.dependencies[DatabaseModule].session() as session:
            query = (await session.execute(select(Item)))
            all_user_ids = [[user.name, user.renters_users_id] for el in query for user in el]
            for el in all_user_ids:
                item = el[0]
                for user_id in el[1]:
                    user_info = await self.bot.api.users.get(user_ids=user_id, fields=["first_name", "last_name"])
                    name = f"{user_info[0].first_name} {user_info[0].last_name}"
                    if name == "DELETED ":
                        deleted_users_ids.append([user_id, item])

        return deleted_users_ids
