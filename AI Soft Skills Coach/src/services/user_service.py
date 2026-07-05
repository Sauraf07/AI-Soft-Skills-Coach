from src.repository.user_repo import UserRepository
from src.repository.user_progress_repo import UserProgressRepository
from src.models.user import User
from src.utils.password import hash_password, verify_password
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.user_progress_repo = UserProgressRepository(session)

    async def register_user(self, user: User):
        existing_user = await self.user_repo.get_user_by_email(user.email)
        if existing_user is not None:
            raise ValueError("An account with this email already exists.")

        user.password = hash_password(user.password)
        created_user = await self.user_repo.create_user(user)
        await self.user_progress_repo.ensure_default_for_user(created_user.id)
        await self.session.commit()
        return created_user

    async def authenticate_user(self, email: str, password: str):
        user = await self.user_repo.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.password):
            return None

        return user

    async def get_user_by_id(self, user_id: int):
        return await self.user_repo.get_user_by_id(user_id)

    async def update_user(self, user_id: int, data: dict):
        if data.get("password"):
            data = {**data, "password": hash_password(data["password"])}
        return await self.user_repo.update_by_id(user_id, data)

    async def delete_user(self, user_id: int):
        return await self.user_repo.delete_by_id(user_id)

    async def list_users(self):
        return await self.user_repo.list_all()
