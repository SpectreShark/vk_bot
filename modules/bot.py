from vkbottle import Bot
from logging import getLogger

from vkbottle.bot import Message

from modules import Module
from modules.config import ConfigModule

LOGGER = getLogger("BotModule")


class VkBotModule(Module):
    bot: Bot
    dependencies = [ConfigModule]

    async def on_load(self) -> None:
        LOGGER.info("Starting up the bot...")
        self.bot = Bot(self.dependencies[0].data.VK_BOT_TOKEN)

        @self.bot.on.message(text="Help me")
        async def on_help_mes(message: Message) -> None:
            await message.reply("Никто тебе не поможет")

        await self.bot.run_polling()
