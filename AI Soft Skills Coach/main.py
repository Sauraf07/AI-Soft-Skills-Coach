from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home/index.html")


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={"message": None}
    )


@app.post("/login")
async def login_submit(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "message": f"Demo login received for {email}. Connect this form to your auth backend next.",
        },
    )


@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={"message": None}
    )


@app.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: Optional[str] = Form(None),
):
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "message": f"Demo registration received for {username}. Connect this form to your auth backend next.",
        },
    )