"""
CRUD operations for database models
"""
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app import db_models


# User operations
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[db_models.User]:
    """Get user by username"""
    result = await db.execute(
        select(db_models.User).where(db_models.User.username == username)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, hashed_password: str) -> db_models.User:
    """Create new user"""
    user = db_models.User(username=username, hashed_password=hashed_password)
    db.add(user)
    await db.flush()
    return user


# Instagram Account operations
async def get_accounts(db: AsyncSession, user_id: int) -> List[db_models.InstagramAccount]:
    """Get all Instagram accounts for user"""
    result = await db.execute(
        select(db_models.InstagramAccount)
        .where(db_models.InstagramAccount.user_id == user_id)
        .order_by(db_models.InstagramAccount.created_at.desc())
    )
    return list(result.scalars().all())


async def get_account_by_username(
    db: AsyncSession, 
    user_id: int, 
    username: str
) -> Optional[db_models.InstagramAccount]:
    """Get Instagram account by username for specific user"""
    result = await db.execute(
        select(db_models.InstagramAccount)
        .where(
            db_models.InstagramAccount.user_id == user_id,
            db_models.InstagramAccount.username == username
        )
    )
    return result.scalar_one_or_none()


async def create_account(
    db: AsyncSession,
    user_id: int,
    username: str,
    followers: int,
    avg_views: int,
    reels_with_10000_views: int
) -> db_models.InstagramAccount:
    """Create new Instagram account"""
    account = db_models.InstagramAccount(
        user_id=user_id,
        username=username,
        followers=followers,
        avg_views=avg_views,
        reels_with_10000_views=reels_with_10000_views
    )
    db.add(account)
    await db.flush()
    return account


async def delete_account(db: AsyncSession, user_id: int, username: str) -> bool:
    """Delete Instagram account"""
    result = await db.execute(
        delete(db_models.InstagramAccount)
        .where(
            db_models.InstagramAccount.user_id == user_id,
            db_models.InstagramAccount.username == username
        )
    )
    return result.rowcount > 0


# Blacklist operations
async def get_blacklist(db: AsyncSession, user_id: int) -> List[db_models.BlacklistAccount]:
    """Get blacklist for user"""
    result = await db.execute(
        select(db_models.BlacklistAccount)
        .where(db_models.BlacklistAccount.user_id == user_id)
        .order_by(db_models.BlacklistAccount.created_at.desc())
    )
    return list(result.scalars().all())


async def add_to_blacklist(db: AsyncSession, user_id: int, username: str) -> db_models.BlacklistAccount:
    """Add account to blacklist"""
    blacklist_entry = db_models.BlacklistAccount(user_id=user_id, username=username)
    db.add(blacklist_entry)
    await db.flush()
    return blacklist_entry


async def remove_from_blacklist(db: AsyncSession, user_id: int, username: str) -> bool:
    """Remove account from blacklist"""
    result = await db.execute(
        delete(db_models.BlacklistAccount)
        .where(
            db_models.BlacklistAccount.user_id == user_id,
            db_models.BlacklistAccount.username == username
        )
    )
    return result.rowcount > 0


async def is_blacklisted(db: AsyncSession, user_id: int, username: str) -> bool:
    """Check if account is blacklisted"""
    result = await db.execute(
        select(db_models.BlacklistAccount)
        .where(
            db_models.BlacklistAccount.user_id == user_id,
            db_models.BlacklistAccount.username == username
        )
    )
    return result.scalar_one_or_none() is not None


# Integration Pending operations
async def get_integration_pending(db: AsyncSession, user_id: int) -> List[db_models.IntegrationPending]:
    """Get pending integrations for user"""
    result = await db.execute(
        select(db_models.IntegrationPending)
        .where(db_models.IntegrationPending.user_id == user_id)
        .order_by(db_models.IntegrationPending.created_at.desc())
    )
    return list(result.scalars().all())


async def add_to_integration_pending(
    db: AsyncSession,
    user_id: int,
    username: str,
    followers: int,
    avg_views: int,
    reels_with_10000_views: int
) -> db_models.IntegrationPending:
    """Add to integration pending"""
    pending = db_models.IntegrationPending(
        user_id=user_id,
        username=username,
        followers=followers,
        avg_views=avg_views,
        reels_with_10000_views=reels_with_10000_views
    )
    db.add(pending)
    await db.flush()
    return pending


async def remove_from_integration_pending(db: AsyncSession, user_id: int, username: str) -> bool:
    """Remove from integration pending"""
    result = await db.execute(
        delete(db_models.IntegrationPending)
        .where(
            db_models.IntegrationPending.user_id == user_id,
            db_models.IntegrationPending.username == username
        )
    )
    return result.rowcount > 0


async def get_integration_pending_by_username(
    db: AsyncSession, user_id: int, username: str
) -> Optional[db_models.IntegrationPending]:
    """Get specific pending integration"""
    result = await db.execute(
        select(db_models.IntegrationPending)
        .where(
            db_models.IntegrationPending.user_id == user_id,
            db_models.IntegrationPending.username == username
        )
    )
    return result.scalar_one_or_none()


# Integration operations
async def get_integrations(db: AsyncSession, user_id: int) -> List[db_models.Integration]:
    """Get all integrations for user"""
    result = await db.execute(
        select(db_models.Integration)
        .where(db_models.Integration.user_id == user_id)
        .order_by(db_models.Integration.created_at.desc())
    )
    return list(result.scalars().all())


async def create_integration(
    db: AsyncSession, user_id: int, username: str, reels: list = None
) -> db_models.Integration:
    """Create new integration"""
    integration = db_models.Integration(
        user_id=user_id,
        username=username,
        reels=reels or []
    )
    db.add(integration)
    await db.flush()
    return integration


async def get_integration_by_username(
    db: AsyncSession, user_id: int, username: str
) -> Optional[db_models.Integration]:
    """Get specific integration"""
    result = await db.execute(
        select(db_models.Integration)
        .where(
            db_models.Integration.user_id == user_id,
            db_models.Integration.username == username
        )
    )
    return result.scalar_one_or_none()


async def update_integration_reels(
    db: AsyncSession, integration: db_models.Integration, reels: list
) -> db_models.Integration:
    """Update integration reels"""
    integration.reels = reels
    await db.flush()
    return integration


async def update_integration_metrics(
    db: AsyncSession,
    integration: db_models.Integration,
    median_views: int,
    median_likes: int,
    median_comments: int
) -> db_models.Integration:
    """Update integration metrics"""
    integration.median_views = median_views
    integration.median_likes = median_likes
    integration.median_comments = median_comments
    await db.flush()
    return integration
