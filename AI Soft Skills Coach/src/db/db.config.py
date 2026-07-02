from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

URL = "mysql+aiomysql://root:root@localhost:3306/ai_softskill"
engine = create_async_engine(URL, echo=True)

Sessionlocal = async_sessionmaker(bind=engine, expire_on_commit=False )
print("DataBase Connected")
class Base(DeclarativeBase):
    pass