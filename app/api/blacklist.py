"""
Blacklist management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlacklistAccount
from app.database import get_db
from app.db_models import User
from app import crud
from app.security import get_current_user

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


@router.get("", response_model=List[BlacklistAccount])
async def get_blacklist(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    blacklist = await crud.get_blacklist(db, current_user.id)
    return [BlacklistAccount(username=acc.username) for acc in blacklist]


@router.post("")
async def add_to_blacklist(
    account: BlacklistAccount,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await crud.add_to_blacklist(db, current_user.id, account.username)
    return {"message": "Account added to blacklist"}


@router.delete("/{username}")
async def remove_from_blacklist(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    removed = await crud.remove_from_blacklist(db, current_user.id, username)
    if not removed:
        raise HTTPException(status_code=404, detail="Account not found in blacklist")
    return {"message": "Account removed from blacklist"}


@router.post("/multiple", response_model=List[BlacklistAccount])
async def add_multiple_to_blacklist(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    usernames = data.get("usernames", [])

    if not usernames:
        raise HTTPException(status_code=400, detail="Usernames are required")

    added_accounts = []
    for username in usernames:
        # Check if already blacklisted
        if not await crud.is_blacklisted(db, current_user.id, username):
            await crud.add_to_blacklist(db, current_user.id, username)
            added_accounts.append(BlacklistAccount(username=username))

    return added_accounts

