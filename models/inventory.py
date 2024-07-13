from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import BaseModel
from models.item import Item


class Inventory(BaseModel):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    item: Mapped[Item] = relationship(back_populates="inventory")
    quantity_on_sunday: Mapped[int] = mapped_column(min=0, default=0)
