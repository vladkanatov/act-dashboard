"""
Integration management endpoints
"""
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InstagramAccount, ReelsPayload, IntegrationsPayload, User
from app.utils import calculate_median
from app.security import get_current_user
from app.core import config
from app.services.instagram import fetch_reels_data_api
from app.database import get_db
from app import crud

router = APIRouter(tags=["integration"])


@router.get("/integration_pending", response_model=List[InstagramAccount])
async def get_integration_pending(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pending = await crud.get_integration_pending(db, current_user.id)
    return [
        InstagramAccount(
            username=item.username,
            followers=item.followers,
            avg_views=item.avg_views,
            reels_with_10000_views=item.reels_with_10000_views
        )
        for item in pending
    ]


@router.post("/move_to_integration_pending/{username}")
async def move_to_integration_pending(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Получаем аккаунт из основной таблицы
    account = await crud.get_account_by_username(db, current_user.id, username)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Добавляем в integration_pending
    await crud.add_to_integration_pending(
        db, 
        current_user.id, 
        username,
        account.followers,
        account.avg_views,
        account.reels_with_10000_views
    )
    
    # Удаляем из основной таблицы аккаунтов
    await crud.delete_account(db, current_user.id, username)
    
    return {"message": "Account moved to integration pending"}


@router.delete("/remove_from_integration_pending/{username}")
async def remove_from_integration_pending(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await crud.remove_from_integration_pending(db, current_user.id, username)
    return {"message": "Account removed from integration pending"}


@router.get("/integration", response_model=List[IntegrationsPayload])
async def get_integration(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    integrations = await crud.get_integrations(db, current_user.id)
    result = []
    
    for integration in integrations:
        account_data = {
            "username": integration.username,
            "reels": integration.reels_data or []
        }
        
        if integration.reels_data:
            views = [reel['views'] for reel in integration.reels_data]
            likes = [reel['likes'] for reel in integration.reels_data]
            comments = [reel['comments'] for reel in integration.reels_data]
            account_data['median_views'] = int(calculate_median(views))
            account_data['median_likes'] = int(calculate_median(likes))
            account_data['median_comments'] = int(calculate_median(comments))
        else:
            account_data['median_views'] = 0
            account_data['median_likes'] = 0
            account_data['median_comments'] = 0
        
        result.append(account_data)
    
    return result


@router.post("/integration/{username}/reels")
async def add_reels_to_integration(
    username: str,
    payload: ReelsPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Получаем или создаем интеграцию
    integration = await crud.get_integration_by_username(db, current_user.id, username)
    if not integration:
        integration = await crud.create_integration(db, current_user.id, username)
    
    # Обновляем рилсы
    reels_data = [r.model_dump() for r in payload.reels]
    await crud.update_integration_reels(db, current_user.id, username, reels_data)
    
    return {"message": "Reels updated successfully"}


@router.post("/move_to_integration/{username}")
async def move_to_integration(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Получаем аккаунт из integration_pending
    pending = await crud.get_integration_pending_by_username(db, current_user.id, username)
    if not pending:
        raise HTTPException(status_code=404, detail="Account not found in integration pending")
    
    # Создаем интеграцию
    await crud.create_integration(db, current_user.id, username)
    
    # Удаляем из pending
    await crud.remove_from_integration_pending(db, current_user.id, username)
    
    return {"message": "Account moved to integration"}


@router.post("/update_reels_data")
async def update_reels_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    integrations = await crud.get_integrations(db, current_user.id)
    
    if not integrations:
        raise HTTPException(status_code=404, detail="No integration accounts found")

    for integration in integrations:
        if integration.reels_data:
            for reel in integration.reels_data:
                url = reel["url"]
                
                # Use the service function that supports debug mode
                reels_data_json = await fetch_reels_data_api(url)
                
                if reels_data_json is None:
                    continue
                    
                reels_data = reels_data_json['data']['metrics']
                reel["views"] = reels_data.get("play_count", 0)
                reel["likes"] = reels_data.get("like_count", 0)
                reel["comments"] = reels_data.get("comment_count", 0)
            
            # Обновляем рилсы в БД
            await crud.update_integration_reels(db, current_user.id, integration.username, integration.reels_data)

    return {"message": "Reels data updated successfully"}


@router.post("/fetch_reels_data")
async def fetch_reels_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    url = data.get('url')
    username = data.get('username')

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Use the service function that supports debug mode
    reels_data_json = await fetch_reels_data_api(url)
    
    if reels_data_json is None:
        raise HTTPException(status_code=400, detail="Failed to fetch reels data")
    
    reels_data = reels_data_json['data']['metrics']

    reel_data = {
        "url": url,
        "views": reels_data.get("play_count", 0),
        "likes": reels_data.get("like_count", 0),
        "comments": reels_data.get("comment_count", 0)
    }

    # Получаем или создаем интеграцию
    integration = await crud.get_integration_by_username(db, current_user.id, username)
    if not integration:
        integration = await crud.create_integration(db, current_user.id, username)
    
    # Добавляем новый рилс к существующим
    current_reels = integration.reels_data or []
    current_reels.append(reel_data)
    await crud.update_integration_reels(db, current_user.id, username, current_reels)

    return reel_data
