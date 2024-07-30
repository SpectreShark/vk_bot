from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete, insert
from sqlalchemy.exc import IntegrityError

from modules import Module
from models import Support, Item
from modules.database import DatabaseModule
from config import support_specialists_ids, initial_inventory_values

from datetime import datetime

from modules.redis import RedisModule


class SchedulerModule(Module):
    scheduler: AsyncIOScheduler
    required_dependencies = [DatabaseModule, RedisModule]

    async def on_load(self) -> None:
        state = await self.dependencies[RedisModule].get_menu(0)
        if (datetime.now().weekday() == 0) and (state == "No"):
            await self.update_database_constants()
        elif datetime.now().weekday() != 0:
            await self.dependencies[RedisModule].set_menu(0, "No")

        self.scheduler = AsyncIOScheduler()

        self.scheduler.add_job(self.update_database_constants, "cron", day_of_week="mon", hour=0, minute=0)
        self.scheduler.start()

    async def update_database_constants(self) -> None:
        await self.dependencies[RedisModule].set_menu(0, "Yes")
        await self.add_technical_support()
        async with self.dependencies[DatabaseModule].session() as session:
            await session.execute(delete(Item))

            for el in initial_inventory_values:
                await session.execute(insert(Item).values(
                    name=el[0],
                    quantity_on_sunday=el[1],
                    price=int(el[2])
                ))

                await session.commit()

    async def add_technical_support(self) -> None:
        async with self.dependencies[DatabaseModule].session() as session:
            try:
                for el in support_specialists_ids:
                    await session.execute(insert(Support).values(
                            user_id=el
                        ))
                    await session.commit()
            except IntegrityError:
                ...