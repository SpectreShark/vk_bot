from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import BaseModel
from models.inventory import Inventory


class Item(BaseModel):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, max_length=255)
    price: Mapped[float] = mapped_column(min=0)
    inventory: Mapped[Inventory] = relationship(back_populates="item")

