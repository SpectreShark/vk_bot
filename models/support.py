# from sqlalchemy.orm import Mapped, mapped_column
#
# from models import BaseModel
#
#
# class Support(BaseModel):
#     __tablename__ = "supports"
#
#     id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
#     user_id: Mapped[int] = mapped_column(unique=True, index=True)