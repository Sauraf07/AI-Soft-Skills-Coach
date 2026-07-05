from sqlalchemy import desc, select

from src.models import Analysis
from src.repository.base_repo import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, session):
        super().__init__(session, Analysis)

    async def get_latest_by_conversation_id(self, conversation_id: int):
        result = await self.session.execute(
            select(Analysis)
            .where(Analysis.conversation_id == conversation_id)
            .order_by(desc(Analysis.created_at), desc(Analysis.id))
            .limit(1)
        )
        return result.scalar_one_or_none()
