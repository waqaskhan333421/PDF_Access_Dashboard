from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.auth import get_current_user, decode_token
from models.user import User

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")


def get_optional_user(request: Request):
    """Try to get current user from cookie, return None if not authenticated."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    payload = decode_token(token)
    if not payload:
        return None
    return payload


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = get_optional_user(request)
    if user:
        role = user.get("role", "user")
        if role == "admin":
            return RedirectResponse(url="/admin-dashboard", status_code=302)
        return RedirectResponse(url="/user-dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    user = get_optional_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@router.get("/admin-requests", response_class=HTMLResponse)
def admin_requests_page(request: Request):
    user = get_optional_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_requests.html", {"request": request})


@router.get("/admin-users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    user = get_optional_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_users.html", {"request": request})


@router.get("/admin-pdfs", response_class=HTMLResponse)
def admin_pdfs_page(request: Request):
    user = get_optional_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_pdfs.html", {"request": request})


@router.get("/user-dashboard", response_class=HTMLResponse)
def user_dashboard_page(request: Request):
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("user_dashboard.html", {"request": request})
