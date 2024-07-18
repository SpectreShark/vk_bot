from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Support(Base):
    __tablename__ = "supports"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
