"""
Authentication endpoints: register, login (token)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Token
from app.database import get_db
from app import crud
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(user: User, db: AsyncSession = Depends(get_db)):
    existing_user = await crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    await crud.create_user(db, user.username, hash_password(user.password))
    return {"message": "User registered successfully"}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

