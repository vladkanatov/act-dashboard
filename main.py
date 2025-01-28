import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
import uvicorn
import jwt
from datetime import timedelta, datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите допустимые источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешите все методы
    allow_headers=["*"],  # Разрешите все заголовки
)
app.mount("/static", StaticFiles(directory="static"), name="static")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100000

RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
RAPIDAPI_KEY = "e548dfe5c6msh388cd314a63a60fp10805bjsn83e6c1254b86"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

# In-memory database simulation
db_users = {}
db_accounts = {}
db_blacklist = {}
db_integration_pending = {}
db_integration = {}


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def get_user(username: str):
    return db_users.get(username)

# Models
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

# Dependency
def get_current_user(token: str = Header(None)):
    if token is None:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return get_user(username)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register")
def register(user: User):
    if user.username in db_users:
        raise HTTPException(status_code=400, detail="User already exists")
    db_users[user.username] = {
        "username": user.username,
        "password": hash_password(user.password),
    }
    db_accounts[user.username] = []
    return {"message": "User registered successfully"}

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/integration_pending", response_model=List[InstagramAccount])
def get_integration_pending(current_user: dict = Depends(get_current_user)):
    return db_integration_pending.get(current_user["username"], [])

@app.post("/move_to_integration_pending/{username}")
def move_to_integration_pending(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user not in db_integration_pending:
        db_integration_pending[user] = []
    account = next((acc for acc in db_accounts[user] if acc["username"] == username), None)
    if account:
        db_integration_pending[user].append(account)
        db_accounts[user] = [acc for acc in db_accounts[user] if acc["username"] != username]
    return {"message": "Account moved to integration pending"}

@app.delete("/remove_from_integration_pending/{username}")
def remove_from_integration_pending(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user in db_integration_pending:
        db_integration_pending[user] = [acc for acc in db_integration_pending[user] if acc["username"] != username]
    return {"message": "Account removed from integration pending"}

def calculate_median(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 0:
        return 0
    if n % 2 == 1:
        return sorted_data[n // 2]
    else:
        return (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2

@app.get("/integration", response_model=List[IntegrationsPayload])
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

@app.post("/integration/{username}/reels")
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

@app.post("/move_to_integration/{username}")
def move_to_integration(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    if user not in db_integration:
        db_integration[user] = []
    account = next((acc for acc in db_integration_pending[user] if acc["username"] == username), None)
    if account:
        db_integration[user].append({"username": account["username"]})
        db_integration_pending[user] = [acc for acc in db_integration_pending[user] if acc["username"] != username]
    return {"message": "Account moved to integration"}

@app.get("/blacklist", response_model=List[BlacklistAccount])
def get_blacklist(current_user: dict = Depends(get_current_user)):
    return db_blacklist.get(current_user["username"], [])

@app.post("/blacklist")
def add_to_blacklist(account: BlacklistAccount, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_blacklist:
        db_blacklist[current_user["username"]] = []
    db_blacklist[current_user["username"]].append(account)
    return {"message": "Account added to blacklist"}

@app.delete("/blacklist/{username}")
def remove_from_blacklist(username: str, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_blacklist:
        raise HTTPException(status_code=404, detail="No blacklist found")
    db_blacklist[current_user["username"]] = [
        acc for acc in db_blacklist[current_user["username"]] if acc['username'] != username
    ]
    return {"message": "Account removed from blacklist"}

@app.post("/blacklist/multiple", response_model=List[BlacklistAccount])
async def add_multiple_to_blacklist(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    usernames = data.get("usernames", [])

    if not usernames:
        raise HTTPException(status_code=400, detail="Usernames are required")

    if current_user["username"] not in db_blacklist:
        db_blacklist[current_user["username"]] = []

    added_accounts = []
    for username in usernames:
        if username not in db_blacklist[current_user["username"]]:
            account = {"username": username}
            db_blacklist[current_user["username"]].append(account)
            added_accounts.append(account)

    return added_accounts

@app.get("/accounts", response_model=List[InstagramAccount])
def get_accounts(current_user: dict = Depends(get_current_user)):
    return db_accounts.get(current_user["username"], [])

@app.post("/accounts")
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

    # db_accounts[current_user["username"]].append({
    #     "username": username,
    #     "followers": 100,
    #     "avg_views": 12,
    #     "reels_with_10000_views": 142
    # })
    # return {"message": "Account added successfully"}


@app.delete("/accounts/{ig_username}")
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

async def process_followings(username, current_user, engagement):

    async with aiohttp.ClientSession() as session:
        # Получаем список followings
        followings_data = await fetch_followings(session, username)
        followings = [item['id'] for item in followings_data['data']['items']]

        tasks = []
        for user_id in followings:
            tasks.append(process_user(session, user_id, engagement, current_user))
        results = await asyncio.gather(*tasks)

        save_to_db(results, current_user["username"])

async def process_user(session, user_id, engagement, current_user):
    # Получаем профиль пользователя
    profile_data = await fetch_profile(session, user_id)
    username = profile_data['data']['username']

    if any(acc['username'] == username for acc in db_blacklist.get(current_user["username"], [])):
        return

    followers_count = profile_data['data']['follower_count']

    if followers_count > 80000:
        return

    # Получаем рилсы
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

def save_to_db(results, username):
    """
    Save processed user data into the database.
    Args:
        results: List of tuples containing (username, followers_count, avg_views, reels_with_10000_views).
        username: The name of the user's table to insert data into.
    """
    if not results:
        print("No valid results to save.")
        return

    if username not in db_accounts:
        db_accounts[username] = []

    for result in results:
        if result:  # Ensure the result is not None
            db_accounts[username].append({
                "username": result[0],
                "followers": result[1],
                "avg_views": result[2],
                "reels_with_10000_views": result[3]
            })

@app.post("/analyze_followings")
async def analyze_followings(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    engagement = data.get("engagement")
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    await process_followings(username, current_user, engagement)
    return {"message": "Accounts analyzed successfully"}

    # if current_user["username"] not in db_accounts:
    #     db_accounts[current_user["username"]] = []

    # for i in range(10):
    #     db_accounts[current_user["username"]].append({
    #             "username": f"Roma_{i}",
    #             "followers": 24122,
    #             "avg_views": 152123,
    #             "reels_with_10000_views": 12314
    #         })
    # return {"message": "Accounts analyzed successfully"}

@app.post("/update_reels_data")
async def update_reels_data(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in db_integration:
        raise HTTPException(status_code=404, detail="No integration accounts found")

    accounts = db_integration[current_user["username"]]
    for account in accounts:
        username = account["username"]
        if "reels" in account:
            for reel in account["reels"]:
                url = reel["url"]
                reels_url = f"https://{RAPIDAPI_HOST}/v1/post_info"
                params = {"code_or_id_or_url": url}

                async with aiohttp.ClientSession() as session:
                    async with session.get(reels_url, headers=HEADERS, params=params) as response:
                        if response.status != 200:
                            continue
                        reels_data_json = await response.json()
                        reels_data = reels_data_json['data']['metrics']

                reel["views"] = reels_data.get("play_count", 0)
                reel["likes"] = reels_data.get("like_count", 0)
                reel["comments"] = reels_data.get("comment_count", 0)

    return {"message": "Reels data updated successfully"}

@app.post("/fetch_reels_data")
async def fetch_reels_data(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    url = data.get('url')
    username = data.get('username')
    reels_url = f"https://{RAPIDAPI_HOST}/v1/post_info"

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    params = {"code_or_id_or_url": url}

    async with aiohttp.ClientSession() as session:
        async with session.get(reels_url, headers=HEADERS, params=params) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch reels data")
            reels_data_json = await response.json()
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

# Frontend HTML serving
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, token: str = None):
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("sub"):
                return templates.TemplateResponse("main.html", {"request": request})
        except jwt.PyJWTError:
            pass
    return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/main", response_class=HTMLResponse)
# def read_main(request: Request):
#     return templates.TemplateResponse("main.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")