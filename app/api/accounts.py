"""
Instagram accounts management endpoints
"""
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from app.models import InstagramAccount
from app.db import db_accounts, db_blacklist
from app.security import get_current_user
from app.core.config import RAPIDAPI_HOST, HEADERS
from app.services.instagram import process_followings

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=List[InstagramAccount])
def get_accounts(current_user: dict = Depends(get_current_user)):
    return db_accounts.get(current_user["username"], [])


@router.post("")
async def add_account(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    username = data.get("username")
    engagement = data.get("engagement")

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    if any(acc['username'] == username for acc in db_blacklist.get(current_user["username"], [])):
        raise HTTPException(status_code=400, detail="Account is blacklisted")

    async with aiohttp.ClientSession() as session:
        profile_url = f"https://{RAPIDAPI_HOST}/v1/info"
        async with session.get(profile_url, headers=HEADERS, params={"username_or_id_or_url": username}) as profile_response:
            if profile_response.status != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch profile information")
            data = await profile_response.json()
            followers_count = data['data']['follower_count']

            if followers_count > 80000:
                raise HTTPException(status_code=400, detail="Too many followers in account")

        reels = []
        pagination_token = None
        for _ in range(4):
            reels_url = f"https://{RAPIDAPI_HOST}/v1.2/reels"
            params = {"username_or_id_or_url": username}
            if pagination_token:
                params["pagination_token"] = pagination_token

            async with session.get(reels_url, headers=HEADERS, params=params) as reels_response:
                if reels_response.status != 200:
                    break
                reels_data = await reels_response.json()

                reels.extend(reels_data['data']['items'])
                pagination_token = reels_data.get('pagination_token')
                if not pagination_token:
                    break

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
        if current_user["username"] not in db_accounts:
            db_accounts[current_user["username"]] = []

        db_accounts[current_user["username"]].append({
            "username": username,
            "followers": followers_count,
            "avg_views": avg_views,
            "reels_with_10000_views": reels_with_10000_views
        })
        return {"message": "Account added successfully"}


@router.delete("/{ig_username}")
def delete_account(ig_username: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    if username not in db_accounts:
        raise HTTPException(status_code=404, detail="No accounts found")
    db_accounts[username] = [
        acc for acc in db_accounts[username] if acc['username'] != ig_username
    ]

    if username not in db_blacklist:
        db_blacklist[username] = []
    db_blacklist[username].append({"username": ig_username})
    return {"message": "Account deleted successfully"}


@router.post("/analyze_followings")
async def analyze_followings(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    engagement = data.get("engagement")
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    await process_followings(username, current_user, engagement)
    return {"message": "Accounts analyzed successfully"}
