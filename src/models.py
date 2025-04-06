from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class InstagramAccount(BaseModel):
    username: str
    followers: int
    avg_views: int
    reels_with_10000_views: int
