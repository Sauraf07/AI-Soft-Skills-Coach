from src.models import UserProgress
from src.repository.base_repo import BaseRepository


class UserProgressRepository(BaseRepository[UserProgress]):
    def __init__(self, session):
        super().__init__(session, UserProgress)

    async def get_by_user_id(self, user_id: int):
        return await self.get_one_by(user_id=user_id)

    async def ensure_default_for_user(self, user_id: int):
        progress = await self.get_by_user_id(user_id)
        if progress is not None:
            return progress

        return await self.create(UserProgress(user_id=user_id))
