import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.utils.deps import ALGORITHM, SECRET_KEY, get_current_user, create_tables, get_db
from passlib.context import CryptContext
from src.utils.token import create_access_token
from src.models import User, Token, InstagramAccount
from src.service import svc_fetch_reels
from typing import List
import jwt

RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
RAPIDAPI_KEY = "e548dfe5c6msh388cd314a63a60fp10805bjsn83e6c1254b86"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

router = APIRouter()
router.mount("/static", StaticFiles(directory="static"), name="static")
@router.on_startup.append(create_tables)

@router.post("/fetch_reels_data")
async def fetch_reels_data(request: Request, current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    data = await request.json()
    url = data.get('url')
    username = data.get('username')
    
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    return svc_fetch_reels(url, current_user, db, username)

@router.get("/integration_pending", response_model=List[InstagramAccount])
async def get_integration_pending(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    # Получаем список аккаунтов в статусе "integration_pending" для текущего пользователя
    user_id = current_user["id"]
    accounts = await db.fetch(
        "SELECT username, followers, avg_views, reels_with_10000_views FROM integration_pending WHERE user_id = $1",
        user_id
    )
    return [InstagramAccount(**account) for account in accounts]

@router.post("/register")
async def register(user: User, db=Depends(get_db)):
    # Проверяем, существует ли пользователь
    existing_user = await db.fetchrow("SELECT username FROM users WHERE username = $1", user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Хэшируем пароль
    hashed_password = pwd_context.hash(user.password)
    
    # Добавляем пользователя в базу данных
    await db.execute(
        "INSERT INTO users (username, password) VALUES ($1, $2)",
        user.username, hashed_password
    )
    
    return {"message": "User registered successfully"}

@router.get("/", response_class=HTMLResponse)
def read_index(request: Request, token: str = None):
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("sub"):
                return templates.TemplateResponse("main.html", {"request": request})
        except jwt.PyJWTError:
            pass
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    # Проверяем, существует ли пользователь
    user = await db.fetchrow("SELECT username, password FROM users WHERE username = $1", form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}