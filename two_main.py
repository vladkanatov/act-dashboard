from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from passlib.context import CryptContext
import uvicorn
import jwt
from datetime import timedelta, datetime

app = FastAPI()

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

# In-memory database simulation
db_users = {}
db_accounts = {}

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

class TokenData(BaseModel):
    username: str

# Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    user = db_users.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

@app.post("/register")
def register(user: User):
    if user.username in db_users:
        raise HTTPException(status_code=400, detail="User already exists")
    db_users[user.username] = {
        "username": user.username,
        "password": hash_password(user.password),
    }
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
    # Замените на свою логику проверки данных пользователя
    if form_data.username != "test" or form_data.password != "test":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/accounts", response_model=List[InstagramAccount])
def get_accounts(current_user: dict = Depends(get_current_user)):
    return db_accounts.get(current_user["username"], [])

@app.post("/accounts")
def add_account(account: InstagramAccount, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    if username not in db_accounts:
        db_accounts[username] = []
    db_accounts[username].append(account)
    return {"message": "Account added successfully"}

@app.delete("/accounts/{ig_username}")
def delete_account(ig_username: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    if username not in db_accounts:
        raise HTTPException(status_code=404, detail="No accounts found")
    db_accounts[username] = [
        acc for acc in db_accounts[username] if acc.username != ig_username
    ]
    return {"message": "Account deleted successfully"}

@app.post("/send_message")
def send_message(ig_username: str, message: str, current_user: dict = Depends(get_current_user)):
    # Simulate message sending
    return {"message": f"Message sent to {ig_username}: {message}"}

@app.get("/analyze_followings/{ig_username}")
def analyze_followings(ig_username: str, current_user: dict = Depends(get_current_user)):
    # Simulate followings analysis
    return {"analysis": f"Analysis for {ig_username}"}

# Frontend HTML serving (optional, for simplicity)
@app.get("/")
def read_root():
    return {"message": "Welcome to Instagram Account Manager! Use the API to manage accounts."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")