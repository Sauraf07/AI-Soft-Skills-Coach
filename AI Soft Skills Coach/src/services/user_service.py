from src.repository.user_repo import UserRepository


class UserService:
    def __init__(self, session):
        self.user_repo = UserRepository(session)

    async def create_user(self,user):
        return await self.user_repo.create_user(user)