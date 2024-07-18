from vkbottle import Bot, API
from logging import getLogger

from handlers import MessageHandler
from modules import Module
from modules.config import ConfigModule
from modules.database import DatabaseModule
from modules.redis import RedisModule

LOGGER = getLogger("BotModule")


class VkBotModule(Module):
    bot: Bot = Bot()
    required_dependencies = [ConfigModule, DatabaseModule, RedisModule]

    async def on_load(self) -> None:
        LOGGER.info("Starting up the bot...")
        self.bot.api = API(self.dependencies[ConfigModule].data.VK_BOT_TOKEN)
        message_handler = MessageHandler(self.dependencies, self.bot)

        self.bot.on.message(text=["Начать", "В главное меню"])(message_handler.on_start_command)

        self.bot.on.message(text="Панель администратора")(message_handler.admin_menu)
        self.bot.on.message(text="Список всей аренды")(message_handler.admin_get_all_rentals)
        self.bot.on.message(text="Отменить аренду человеку")(message_handler.admin_cancel_rental)
        self.bot.on.message(text="Добавить тех. специалиста")(message_handler.admin_add_tech_support)
        # self.bot.on.message(text="Удалить тех. специалиста")(message_handler) # TODO: подумать на реализацией

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
