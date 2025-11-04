"""
Instagram accounts management endpoints
"""
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InstagramAccount
from app.database import get_db
from app.db_models import User
from app import crud
from app.security import get_current_user
from app.core import config
from app.services.instagram import process_followings, fetch_profile, fetch_reels

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=List[InstagramAccount])
async def get_accounts(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    accounts = await crud.get_accounts(db, current_user.id)
    return [
        InstagramAccount(
            username=acc.username,
            followers=acc.followers,
            avg_views=acc.avg_views,
            reels_with_10000_views=acc.reels_with_10000_views
        )
        for acc in accounts
    ]


@router.post("")
async def add_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    username = data.get("username")
    engagement = data.get("engagement")
    
    if config.DEBUG_MODE:
        print(f"🔧 DEBUG: Processing account {username} with engagement {engagement}")
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    if await crud.is_blacklisted(db, current_user.id, username):
        raise HTTPException(status_code=400, detail="Account is blacklisted")

    async with aiohttp.ClientSession() as session:
        # Fetch profile using the service function (supports debug mode)
        profile_data = await fetch_profile(session, username)
        followers_count = profile_data['data']['follower_count']

        if followers_count > 80000:
            raise HTTPException(status_code=400, detail="Too many followers in account")

        # Fetch reels using the service function (supports debug mode)
        reels = await fetch_reels(session, username, max_pages=4)

        if engagement:
            engagements = [(reel['like_count'] + reel['comment_count']) / followers_count * 100 for reel in reels]
            median_engagement = sorted(engagements)[len(engagements) // 2] if engagements else 0
            if median_engagement < int(engagement):
                raise HTTPException(status_code=400, detail="Engagement is too low")

        if not reels:
            raise HTTPException(status_code=400, detail="No reels found for this account")

        views = [reel['play_count'] for reel in reels if 'play_count' in reel]
        avg_views = int(sum(views) / len(views))
        reels_with_10000_views = sum(1 for view in views if view > 10000)

        if reels_with_10000_views < 3:
            raise HTTPException(status_code=400, detail="Few reels with 10k views")

        if avg_views < 3000:
            raise HTTPException(status_code=400, detail="Few avg views")

        # Save to database
        await crud.create_account(
            db,
            user_id=current_user.id,
            username=username,
            followers=followers_count,
            avg_views=avg_views,
            reels_with_10000_views=reels_with_10000_views
        )
        
        if config.DEBUG_MODE:
            print(f"🔧 DEBUG: Account {username} added successfully (followers: {followers_count}, avg_views: {avg_views})")
        
        return {"message": "Account added successfully"}


@router.delete("/{ig_username}")
async def delete_account(
    ig_username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Delete account
    deleted = await crud.delete_account(db, current_user.id, ig_username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Add to blacklist
    await crud.add_to_blacklist(db, current_user.id, ig_username)
    return {"message": "Account deleted successfully"}


@router.post("/analyze_followings")
async def analyze_followings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    engagement = data.get("engagement")
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    # Process followings with database session passed in user dict for compatibility
    user_dict = {"username": current_user.username, "id": current_user.id, "db": db}
    await process_followings(username, user_dict, engagement)
    return {"message": "Accounts analyzed successfully"}

