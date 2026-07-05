from sqlalchemy import select

from src.models import User
from src.repository.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def create_user(self, user: User):
        return await self.create(user)

    async def get_user_by_email(self, email: str):
        return await self.get_one_by(email=email)

    async def get_user_by_username(self, username: str):
        return await self.get_one_by(username=username)

    async def get_user_by_id(self, user_id: int):
        return await self.get_by_id(user_id)
