from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.db.db_config import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    native_language: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=func.current_timestamp()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=func.current_timestamp()
    )

    conversations = relationship("Conversation", back_populates="user")
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    learning_goals = relationship("LearningGoal", back_populates="user")
    vocabulary_words = relationship("VocabularyWord", back_populates="user")
    vocabulary_progress = relationship("VocabularyProgress", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
