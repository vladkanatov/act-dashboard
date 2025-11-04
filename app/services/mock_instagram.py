"""
Mock Instagram API responses for debug mode
"""
import random
from typing import List, Dict, Any, Optional


# Mock data generators
def generate_mock_profile(username: str) -> Dict[str, Any]:
    """Generate mock Instagram profile data"""
    return {
        "data": {
            "username": username,
            "follower_count": random.randint(5000, 70000),
            "following_count": random.randint(100, 5000),
            "media_count": random.randint(50, 500),
            "biography": f"Mock bio for {username}",
            "full_name": username.title(),
            "is_verified": random.choice([True, False]),
        }
    }


def generate_mock_reel() -> Dict[str, Any]:
    """Generate a single mock reel"""
    return {
        "id": f"mock_reel_{random.randint(1000, 9999)}",
        "play_count": random.randint(3000, 100000),
        "like_count": random.randint(100, 10000),
        "comment_count": random.randint(10, 1000),
        "caption": "Mock reel caption",
        "taken_at": 1699000000,
    }


def generate_mock_reels(count: int = 12) -> Dict[str, Any]:
    """Generate mock reels response"""
    reels = [generate_mock_reel() for _ in range(count)]
    return {
        "data": {
            "items": reels
        },
        "pagination_token": None if count < 12 else f"mock_token_{random.randint(100, 999)}"
    }


def generate_mock_followings(username: str, count: int = 20) -> Dict[str, Any]:
    """Generate mock followings list"""
    followings = [
        {
            "id": f"mock_user_{i}",
            "username": f"mock_user_{i}",
            "full_name": f"Mock User {i}",
        }
        for i in range(count)
    ]
    return {
        "data": {
            "items": followings
        }
    }


def generate_mock_post_metrics(url: str) -> Dict[str, Any]:
    """Generate mock post/reel metrics"""
    return {
        "data": {
            "metrics": {
                "play_count": random.randint(5000, 50000),
                "like_count": random.randint(200, 5000),
                "comment_count": random.randint(20, 500),
            }
        }
    }


# Mock async functions that mimic the real API
async def mock_fetch_profile(session, user_id: str) -> Dict[str, Any]:
    """Mock version of fetch_profile"""
    return generate_mock_profile(user_id)


async def mock_fetch_reels(session, user_id: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Mock version of fetch_reels"""
    all_reels = []
    for page in range(min(max_pages, 3)):
        reels_data = generate_mock_reels(count=12 if page < 2 else 8)
        all_reels.extend(reels_data['data']['items'])
    return all_reels


async def mock_fetch_followings(session, username: str) -> Dict[str, Any]:
    """Mock version of fetch_followings"""
    return generate_mock_followings(username, count=random.randint(15, 30))


async def mock_fetch_reels_data_api(url: str) -> Dict[str, Any]:
    """Mock version of fetch_reels_data_api"""
    return generate_mock_post_metrics(url)


async def mock_process_user(session, user_id: str, engagement: Optional[str], current_user: dict):
    """Mock version of process_user"""
    profile_data = await mock_fetch_profile(session, user_id)
    username = profile_data['data']['username']
    followers_count = profile_data['data']['follower_count']

    if followers_count > 80000:
        return None

    reels = await mock_fetch_reels(session, user_id)
    # Remove first 2 reels as in original
    del reels[:2]

    views = [reel['play_count'] for reel in reels if 'play_count' in reel]
    avg_views = int(sum(views) / len(views)) if views else 0
    reels_with_10000_views = sum(1 for view in views if view > 10000)

    if reels_with_10000_views < 3:
        return None

    if avg_views < 3000:
        return None

    if engagement:
        engagements = [(reel['like_count'] + reel['comment_count']) / followers_count * 100 for reel in reels]
        median_engagement = sorted(engagements)[len(engagements) // 2] if engagements else 0
        if median_engagement < int(engagement):
            return None

    return (username, followers_count, avg_views, reels_with_10000_views)
