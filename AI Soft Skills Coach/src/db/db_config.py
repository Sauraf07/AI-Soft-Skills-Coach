import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

# Read from .env; fall back to the local default so the project still runs
_raw_url = os.getenv("DATABASE_URL", "mysql+aiomysql://root:root@localhost:3306/ai_softskill")

# Ensure the async driver is used (replace mysql+pymysql or plain mysql with mysql+aiomysql)
if _raw_url.startswith("mysql://") or _raw_url.startswith("mysql+pymysql://"):
    _raw_url = _raw_url.replace("mysql://", "mysql+aiomysql://", 1).replace(
        "mysql+pymysql://", "mysql+aiomysql://", 1
    )

URL = _raw_url
engine = create_async_engine(URL, echo=False)

Sessionlocal = async_sessionmaker(bind=engine, expire_on_commit=False )
print("DataBase Connected")

class Base(DeclarativeBase):
    pass