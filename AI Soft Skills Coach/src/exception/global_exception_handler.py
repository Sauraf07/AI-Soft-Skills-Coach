from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from src.exception.resouce_not_found_exception import ResourceNotFoundException

templates = Jinja2Templates(directory="src/templates")


def is_json_request(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return (
        "application/json" in accept 
        or request.url.path.startswith("/dashboard/message")
        or request.url.path.startswith("/conversation")
    )


def resource_not_found_exception_handler(
    request: Request, exc: ResourceNotFoundException
):
    if is_json_request(request):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": exc.message}
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"request": request, "message": exc.message},
        status_code=404,
    )


def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    if is_json_request(request):
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Database error: " + str(exc)}
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"request": request, "message": str(exc)},
        status_code=500,
    )


def global_exception_handler(request: Request, exc: Exception):
    if is_json_request(request):
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc)}
        )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"request": request, "message": str(exc)},
        status_code=500,
    )

