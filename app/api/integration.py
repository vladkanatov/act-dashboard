"""
Integration management endpoints
"""
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from app.models import InstagramAccount, ReelsPayload, IntegrationsPayload
from app.db import db_integration, db_integration_pending, db_accounts, calculate_median
from app.security import get_current_user
from app.core import config
from app.services.instagram import fetch_reels_data_api

router = APIRouter(tags=["integration"])


@router.get("/integration_pending", response_model=List[InstagramAccount])
def get_integration_pending(current_user: dict = Depends(get_current_user)):
    return db_integration_pending.get(current_user["username"], [])


@router.post("/move_to_integration_pending/{username}")
def move_to_integration_pending(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user not in db_integration_pending:
        db_integration_pending[user] = []
    account = next((acc for acc in db_accounts[user] if acc["username"] == username), None)
    if account:
        db_integration_pending[user].append(account)
        db_accounts[user] = [acc for acc in db_accounts[user] if acc["username"] != username]
    return {"message": "Account moved to integration pending"}


@router.delete("/remove_from_integration_pending/{username}")
def remove_from_integration_pending(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user in db_integration_pending:
        db_integration_pending[user] = [acc for acc in db_integration_pending[user] if acc["username"] != username]
    return {"message": "Account removed from integration pending"}


@router.get("/integration", response_model=List[IntegrationsPayload])
def get_integration(current_user: dict = Depends(get_current_user)):
    accounts = db_integration.get(current_user["username"], [])
    for account in accounts:
        if "reels" in account:
            views = [reel['views'] for reel in account['reels']]
            likes = [reel['likes'] for reel in account['reels']]
            comments = [reel['comments'] for reel in account['reels']]
            account['median_views'] = int(calculate_median(views))
            account['median_likes'] = int(calculate_median(likes))
            account['median_comments'] = int(calculate_median(comments))
        else:
            account['median_views'] = 0
            account['median_likes'] = 0
            account['median_comments'] = 0
            account['reels'] = []
    return accounts


@router.post("/integration/{username}/reels")
def add_reels_to_integration(username: str, payload: ReelsPayload, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user not in db_integration:
        db_integration[user] = []
    account = next((acc for acc in db_integration[user] if acc["username"] == username), None)
    if not account:
        account = {"username": username, "reels": []}
        db_integration[user].append(account)

    # Перезаписываем рилсы из запроса
    account["reels"] = [r.model_dump() for r in payload.reels]
    return {"message": "Reels updated successfully"}


@router.post("/move_to_integration/{username}")
def move_to_integration(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user not in db_integration:
        db_integration[user] = []
    account = next((acc for acc in db_integration_pending[user] if acc["username"] == username), None)
    if account:
        db_integration[user].append({"username": account["username"]})
        db_integration_pending[user] = [acc for acc in db_integration_pending[user] if acc["username"] != username]
    return {"message": "Account moved to integration"}


@router.post("/update_reels_data")
async def update_reels_data(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_integration:
        raise HTTPException(status_code=404, detail="No integration accounts found")

    accounts = db_integration[current_user["username"]]
    for account in accounts:
        username = account["username"]
        if "reels" in account:
            for reel in account["reels"]:
                url = reel["url"]
                
                # Use the service function that supports debug mode
                reels_data_json = await fetch_reels_data_api(url)
                
                if reels_data_json is None:
                    continue
                    
                reels_data = reels_data_json['data']['metrics']
                reel["views"] = reels_data.get("play_count", 0)
                reel["likes"] = reels_data.get("like_count", 0)
                reel["comments"] = reels_data.get("comment_count", 0)

    return {"message": "Reels data updated successfully"}


@router.post("/fetch_reels_data")
async def fetch_reels_data(request: Request, current_user: dict = Depends(get_current_user)):
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

    data = {
        "url": url,
        "views": reels_data.get("play_count", 0),
        "likes": reels_data.get("like_count", 0),
        "comments": reels_data.get("comment_count", 0)
    }

    if current_user["username"] not in db_integration:
        db_integration[current_user["username"]] = []

    account = next((acc for acc in db_integration[current_user["username"]] if acc["username"] == username), None)
    if account:
        if "reels" not in account:
            account["reels"] = []
        account["reels"].append(data)
    else:
        db_integration[current_user["username"]].append({
            "username": username,
            "reels": [data]
        })

    return data
