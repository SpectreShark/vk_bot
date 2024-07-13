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
        message_handler = MessageHandler(self.dependencies)
        # TODO: сделать декораторы на проверку state Redis
        self.bot.on.message(text="В главное меню")(message_handler.on_start_command)
        self.bot.on.message(text="Информация")(message_handler.information)
        self.bot.on.message(text="Аренда")(message_handler.lease)
        self.bot.on.message(text="Помощь")(message_handler.help_menu)
        self.bot.on.message()(message_handler.on_unknown_command)

        await self.bot.run_polling()
