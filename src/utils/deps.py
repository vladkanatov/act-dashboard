from fastapi import Header, HTTPException
import jwt
import asyncpg
from decouple import config



SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100000

async def get_db():
    return await asyncpg.connect(config("DATABASE_URL"))

async def get_user(username: str, db):
    return await db.fetchrow("SELECT * FROM users WHERE username = $1", username)

def get_current_user(db: asyncpg.Connection = get_db(), token: str = Header(None), ):
    if token is None:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return get_user(username, db)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
# DATABASE_URL = "postgresql://user:password@localhost:5432/mydatabase"
async def create_tables():
    conn = await asyncpg.connect(config("DATABASE_URL"))
    try:
        await conn.execute(
            """
            -- Users table
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Blacklist table
            CREATE TABLE blacklist (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                username VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, username)
            );

            -- Accounts table
            CREATE TABLE accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                username VARCHAR(50) NOT NULL,
                followers INTEGER NOT NULL,
                avg_views INTEGER NOT NULL,
                reels_with_10000_views INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, username)
            );

            -- Integration pending table
            CREATE TABLE integration_pending (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                username VARCHAR(50) NOT NULL,
                followers INTEGER NOT NULL,
                avg_views INTEGER NOT NULL,
                reels_with_10000_views INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, username)
            );

            -- Integration table
            CREATE TABLE integrations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                username VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, username)
            );

            -- Reels table
            CREATE TABLE reels (
                id SERIAL PRIMARY KEY,
                integration_id INTEGER REFERENCES integrations(id) ON DELETE CASCADE,
                url VARCHAR(255) NOT NULL,
                views INTEGER NOT NULL,
                likes INTEGER NOT NULL,
                comments INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(integration_id, url)
            );
            """
        )
    finally:
        conn.close()