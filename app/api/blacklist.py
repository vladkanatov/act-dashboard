"""
Blacklist management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from app.models import BlacklistAccount
from app.db import db_blacklist
from app.security import get_current_user

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


@router.get("", response_model=List[BlacklistAccount])
def get_blacklist(current_user: dict = Depends(get_current_user)):
    return db_blacklist.get(current_user["username"], [])


@router.post("")
def add_to_blacklist(account: BlacklistAccount, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_blacklist:
        db_blacklist[current_user["username"]] = []
    db_blacklist[current_user["username"]].append(account)
    return {"message": "Account added to blacklist"}


@router.delete("/{username}")
def remove_from_blacklist(username: str, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_blacklist:
        raise HTTPException(status_code=404, detail="No blacklist found")
    db_blacklist[current_user["username"]] = [
        acc for acc in db_blacklist[current_user["username"]] if acc['username'] != username
    ]
    return {"message": "Account removed from blacklist"}


@router.post("/multiple", response_model=List[BlacklistAccount])
async def add_multiple_to_blacklist(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    usernames = data.get("usernames", [])

    if not usernames:
        raise HTTPException(status_code=400, detail="Usernames are required")

    if current_user["username"] not in db_blacklist:
        db_blacklist[current_user["username"]] = []

    added_accounts = []
    for username in usernames:
        if username not in db_blacklist[current_user["username"]]:
            account = {"username": username}
            db_blacklist[current_user["username"]].append(account)
            added_accounts.append(account)

    return added_accounts
