from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.conversation import Conversation
from src.repository.conversation_repo import ConversationRepository

class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ConversationRepository(session)

    async def create_new_conversation(self, user_id: int) -> Conversation:
        # Create a new conversation with initial values
        new_conv = Conversation(
            user_id=user_id,
            topic="New Conversation",
            start_time=datetime.now(),
            status="in_progress",
            end_time=None,
            duration_seconds=None
        )
        created_conv = await self.conversation_repo.create(new_conv)
        await self.session.commit()
        return created_conv

    async def get_user_conversations(self, user_id: int):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at), desc(Conversation.id))
        )
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: int, user_id: int):
        from fastapi import HTTPException
        from src.models.message import Message

        # Fetch conversation
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify ownership
        if conv.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this conversation")

        # Fetch messages in chronological order (ASC)
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        messages = list(result.scalars().all())

        return {
            "conversation": {
                "id": conv.id,
                "topic": conv.topic,
                "status": conv.status,
                "created_at": conv.created_at
            },
            "messages": [
                {
                    "sender": "AI" if msg.sender == "ai" else "USER",
                    "message": msg.message_text,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        }
