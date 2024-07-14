# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from models import BaseModel
# from models.item import Item
#
#
# class User_Item(BaseModel):
#     __tablename__ = "user_item"
#
#     id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
#     name: Mapped[str] = mapped_column(unique=False, max_length=255)
#     item: Mapped[Item] = relationship(back_populates="inventory")