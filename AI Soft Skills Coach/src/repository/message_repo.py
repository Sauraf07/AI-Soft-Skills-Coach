from sqlalchemy import asc, select

from src.models import Message
from src.repository.base_repo import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session):
        super().__init__(session, Message)

    async def get_by_conversation_id(self, conversation_id: int):
        """Return messages in chronological order (oldest first) for correct chat display."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at), asc(Message.id))
        )
        return list(result.scalars().all())
