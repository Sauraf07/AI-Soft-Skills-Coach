import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError

from src.exception.global_exception_handler import (
    global_exception_handler,
    resource_not_found_exception_handler,
    sqlalchemy_exception_handler,
)
from src.exception.resouce_not_found_exception import ResourceNotFoundException
from src.middleware.auth import Auth

from src.routes.home import router as home_router
from src.routes.auth import router as auth_router
from src.routes.dashboard import router as dashboard_router
from src.routes.conversation import router as conversation_router

app = FastAPI()

app.add_middleware(Auth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "dev-session-secret-key"),
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.add_exception_handler(
    ResourceNotFoundException, resource_not_found_exception_handler
)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(home_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(conversation_router)
