from pydantic import BaseModel
from typing import List


class User(BaseModel):
    username: str
    password: str


class InstagramAccount(BaseModel):
    username: str
    followers: int
    avg_views: int
    reels_with_10000_views: int


class ReelData(BaseModel):
    url: str
    views: int
    likes: int
    comments: int


class ReelsPayload(BaseModel):
    reels: List[ReelData]


class IntegrationAccout(BaseModel):
    username: str


class IntegrationsPayload(BaseModel):
    username: str
    median_views: int
    median_likes: int
    median_comments: int
    reels: List[ReelData]


class TokenData(BaseModel):
    username: str


class BlacklistAccount(BaseModel):
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str
