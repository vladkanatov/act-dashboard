import aiohttp
import asyncio
from typing import List
from ..app.core import config as cfg  # fallback if used as package
from .core import config as _cfg  # type: ignore
from .db import save_to_db, db_blacklist, db_accounts, db_integration

# The above import patterns try to be resilient to package import styles.
# Use config values from app.core.config via relative import when resolved.
try:
    from app.core.config import RAPIDAPI_HOST, HEADERS
except Exception:
    try:
        RAPIDAPI_HOST = _cfg.RAPIDAPI_HOST
        HEADERS = _cfg.HEADERS
    except Exception:
        # Last resort default values (should be overridden by config)
        RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
        HEADERS = {}


async def fetch_followings(session, username):
    url = f"https://{RAPIDAPI_HOST}/v1/following"
    async with session.get(url, headers=HEADERS, params={"username_or_id_or_url": username}) as response:
        return await response.json()


async def fetch_profile(session, user_id):
    url = f"https://{RAPIDAPI_HOST}/v1/info"
    async with session.get(url, headers=HEADERS, params={"username_or_id_or_url": user_id}) as response:
        return await response.json()


async def fetch_reels(session, user_id, max_pages=3):
    reels = []
    pagination_token = None
    for _ in range(max_pages):
        url = f"https://{RAPIDAPI_HOST}/v1.2/reels"
        params = {"username_or_id_or_url": user_id}
        if pagination_token:
            params["pagination_token"] = pagination_token
        async with session.get(url, headers=HEADERS, params=params) as response:
            if response.status != 200:
                break
            data = await response.json()
            reels.extend(data['data']['items'])
            pagination_token = data.get('pagination_token')
            if not pagination_token:
                break
    return reels


async def process_user(session, user_id, engagement, current_user):
    profile_data = await fetch_profile(session, user_id)
    username = profile_data['data']['username']

    if any(acc['username'] == username for acc in db_blacklist.get(current_user["username"], [])):
        return

    followers_count = profile_data['data']['follower_count']

    if followers_count > 80000:
        return

    reels = await fetch_reels(session, user_id)
    del reels[:2]

    views = [reel['play_count'] for reel in reels if 'play_count' in reel]
    avg_views = int(sum(views) / len(views)) if views else 0
    reels_with_10000_views = sum(1 for view in views if view > 10000)

    if reels_with_10000_views < 3:
        return

    if avg_views < 3000:
        return

    if engagement:
        engagements = [(reel['like_count'] + reel['comment_count']) / followers_count * 100 for reel in reels]
        median_engagement = sorted(engagements)[len(engagements) // 2] if engagements else 0
        if median_engagement < int(engagement):
            return

    return (username, followers_count, avg_views, reels_with_10000_views)


async def process_followings(username, current_user, engagement):
    async with aiohttp.ClientSession() as session:
        followings_data = await fetch_followings(session, username)
        followings = [item['id'] for item in followings_data['data']['items']]

        tasks = []
        for user_id in followings:
            tasks.append(process_user(session, user_id, engagement, current_user))
        results = await asyncio.gather(*tasks)

        save_to_db(results, current_user["username"])


async def fetch_reels_data_api(url: str):
    reels_url = f"https://{RAPIDAPI_HOST}/v1/post_info"
    params = {"code_or_id_or_url": url}
    async with aiohttp.ClientSession() as session:
        async with session.get(reels_url, headers=HEADERS, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()
