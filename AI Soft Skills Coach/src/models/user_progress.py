from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.db.db_config import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, unique=True
    )
    total_conversations: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    total_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    average_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("0.00")
    )
    current_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_conversation_at: Mapped[DateTime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=func.current_timestamp()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=func.current_timestamp()
    )

    user = relationship("User", back_populates="progress")
