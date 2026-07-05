import asyncio
from src.db.db_config import Sessionlocal
from src.services.user_service import UserService
from src.utils.password import hash_password
from sqlalchemy import text

async def update_pass():
    async with Sessionlocal() as session:
        # Update user password for testuser@example.com
        res = await session.execute(text("SELECT id, email, password FROM user WHERE email = 'testuser@example.com'"))
        user = res.first()
        if user:
            print("Current user data:", user)
            new_pwd = hash_password("password123")
            await session.execute(text("UPDATE user SET password = :password WHERE id = :id"), {"password": new_pwd, "id": user.id})
            await session.commit()
            print("Password updated successfully!")
        else:
            print("testuser@example.com not found!")

if __name__ == "__main__":
    asyncio.run(update_pass())
