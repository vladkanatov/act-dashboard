import aiohttp
from fastapi import HTTPException
from src.router import HEADERS, RAPIDAPI_HOST


async def svc_fetch_reels(url: str, current_user: dict, db, username: str) -> dict:
    async with aiohttp.ClientSession() as session:
        reels_url = f"https://{RAPIDAPI_HOST}/v1/post_info"
        params = {"code_or_id_or_url": url}
        
        async with session.get(reels_url, headers=HEADERS, params=params) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch reels data")
            reels_data_json = await response.json()
            reels_data = reels_data_json['data']['metrics']
    
    reel_info = {
        "url": url,
        "views": reels_data.get("play_count", 0),
        "likes": reels_data.get("like_count", 0),
        "comments": reels_data.get("comment_count", 0)
    }
    
    # Get or create integration account
    integration = await db.fetchrow(
        "SELECT id FROM integrations WHERE user_id = $1 AND username = $2",
        current_user["id"], username
    )
    
    if not integration:
        integration_id = await db.fetchval(
            "INSERT INTO integrations (user_id, username) VALUES ($1, $2) RETURNING id",
            current_user["id"], username
        )
    else:
        integration_id = integration["id"]
    
    # Insert or update reel
    await db.execute(
        """INSERT INTO reels (integration_id, url, views, likes, comments) 
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (integration_id, url) 
        DO UPDATE SET views = EXCLUDED.views, likes = EXCLUDED.likes, comments = EXCLUDED.comments""",
        integration_id, url, reel_info["views"], reel_info["likes"], reel_info["comments"]
    )
    
    return reel_info
