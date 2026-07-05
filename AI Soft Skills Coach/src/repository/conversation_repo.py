from sqlalchemy import desc, select

from src.models import Conversation
from src.repository.base_repo import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session):
        super().__init__(session, Conversation)

    async def get_recent_by_user(self, user_id: int, limit: int = 3):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at), desc(Conversation.id))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_user(self, user_id: int):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at), desc(Conversation.id))
            .limit(1)
        )
        return result.scalar_one_or_none()
