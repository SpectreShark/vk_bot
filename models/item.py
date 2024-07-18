from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


# содержит название каждого элемента, что можно забронировать, а также его цену


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)

    name: Mapped[str] = mapped_column(unique=True)
    price: Mapped[int] = mapped_column()
    quantity_on_sunday: Mapped[int] = mapped_column()

    renters_users_id = mapped_column(ARRAY(Integer), default=[])
