from typing import Optional
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.db.db_config import Sessionlocal
from src.models.user import User
from src.services.user_service import UserService
from src.utils.session import clear_user_session, start_user_session

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

@router.get("/login")
async def login_page(request: Request, message: Optional[str] = None, error: Optional[str] = None):
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={"message": message, "error": error}
    )

@router.post("/login")
async def login_submit(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    async with Sessionlocal() as session:
        user_service = UserService(session)
        user = await user_service.authenticate_user(email=email, password=password)

        if not user:
            return templates.TemplateResponse(
                request=request,
                name="auth/login.html",
                context={"error": "Invalid email or password."},
                status_code=400,
            )

        start_user_session(request.session, user)
        return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/register")
async def register_page(request: Request, message: Optional[str] = None, error: Optional[str] = None):
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={"message": message, "error": error}
    )

@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: Optional[str] = Form(None),
    native_language: str = Form(...),
):
    async with Sessionlocal() as session:
        user_service = UserService(session)

        user = User(
            username=username,
            email=email,
            password=password,
            profile_image=profile_image or "",
            native_language=native_language,
        )

        try:
            user = await user_service.register_user(user)
        except ValueError as exc:
            return templates.TemplateResponse(
                request=request,
                name="auth/register.html",
                context={"error": str(exc)},
                status_code=400,
            )

        import urllib.parse
        success_msg = urllib.parse.quote("Registration successful! Please log in with your credentials.")
        return RedirectResponse(url=f"/login?message={success_msg}", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    clear_user_session(request.session)
    return RedirectResponse(url="/login", status_code=303)
