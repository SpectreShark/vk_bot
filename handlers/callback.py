from vkbottle.bot import MessageEvent


async def callback_handler(self, event: MessageEvent):
    if event.payload["type"] == "button_press":
        await event.edit_message("Button pressed!")
        await event.show_snackbar("You pressed the button!")
