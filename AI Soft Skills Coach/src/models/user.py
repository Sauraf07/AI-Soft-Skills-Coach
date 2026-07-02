from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.sql.functions import func

from src.db.db_config import Base


class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    username:Mapped[int] = mapped_column(String(100),nullable=False)
    email:Mapped[int] = mapped_column(String(100),nullable=False,unique=True)
    password:Mapped[int] = mapped_column(String(100))
    profile_image:Mapped[int] = mapped_column(String(100))
    native_language:Mapped[int] = mapped_column(String(100))
    created_at:Mapped[DateTime] = mapped_column(DateTime,server_default=func.now())
    updated_at:Mapped[DateTime] = mapped_column(DateTime,server_default=func.now())
