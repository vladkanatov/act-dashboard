from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import aiohttp

from app.security import get_current_user, verify_password, hash_password, create_access_token
from app.models import (
    User,
    InstagramAccount,
    ReelData,
    ReelsPayload,
    IntegrationsPayload,
    Token,
    BlacklistAccount,
)
from app.db import (
    db_accounts,
    db_blacklist,
    db_integration,
    db_integration_pending,
    db_users,
    get_user,
    calculate_median,
    save_to_db,
)
from app.core.config import RAPIDAPI_HOST, HEADERS
from app.services.instagram import (
    fetch_reels,
    fetch_profile,
    fetch_followings,
    process_followings,
    fetch_reels_data_api,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/register")
def register(user: User):
    if user.username in db_users:
        raise HTTPException(status_code=400, detail="User already exists")
    db_users[user.username] = {
        "username": user.username,
        "password": hash_password(user.password),
    }
    db_accounts[user.username] = []
    return {"message": "User registered successfully"}


@router.post("/token", response_model=Token)
def login(form_data: Depends):
    # keep compatibility with original signature in simplified form
    raise HTTPException(status_code=501, detail="Use original /token signature via OAuth2 form")


@router.get("/", response_class=HTMLResponse)
def read_index(request: Request, token: str = None):
    if token:
        try:
            import jwt
            from app.core.config import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("sub"):
                return templates.TemplateResponse("main.html", {"request": request})
        except Exception:
            pass
    return templates.TemplateResponse("index.html", {"request": request})
