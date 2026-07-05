from sqlalchemy import DateTime, Enum, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.db.db_config import Base


class VocabularyProgress(Base):
    __tablename__ = "vocabulary_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word_id: Mapped[int] = mapped_column(
        ForeignKey("vocabulary_words.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("new", "learning", "known", name="vocabulary_progress_status"),
        nullable=False,
        server_default=text("'new'"),
    )
    review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    word = relationship("VocabularyWord", back_populates="progress_entries")
    user = relationship("User", back_populates="vocabulary_progress")
