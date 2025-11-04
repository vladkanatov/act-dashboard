"""
Frontend HTML serving endpoints
"""
import jwt
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="templates")


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
