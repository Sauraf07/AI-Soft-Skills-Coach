from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.db.db_config import Sessionlocal
from src.services.user_service import UserService
from src.utils.session import (
    SESSION_IS_LOGGED_IN,
    SESSION_USER_ID,
    clear_user_session,
)


class Auth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        public_urls = {
            "/",
            "/login",
            "/register",
            "/logout",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
        requested_url = request.url.path

        if requested_url.startswith("/static") or requested_url in public_urls:
            return await call_next(request)

        if not request.session.get(SESSION_IS_LOGGED_IN):
            return RedirectResponse("/login", status_code=303)

        user_id = request.session.get(SESSION_USER_ID)
        if user_id is None:
            clear_user_session(request.session)
            return RedirectResponse("/login", status_code=303)

        async with Sessionlocal() as session:
            user_service = UserService(session)
            current_user = await user_service.get_user_by_id(user_id)

        if current_user is None:
            clear_user_session(request.session)
            return RedirectResponse("/login", status_code=303)

        request.state.current_user = current_user
        return await call_next(request)
