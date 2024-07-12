from modules import Module
from logging import basicConfig, getLogger

LOGGER = getLogger("LoggingModule")


class LoggingModule(Module):
    async def on_load(self, level: int) -> None:
        basicConfig(level=level)
        LOGGER.info(f"Logger was successfully initialized with level {level}.")
