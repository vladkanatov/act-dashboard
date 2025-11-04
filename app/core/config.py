from datetime import timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100000

RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
RAPIDAPI_KEY = "e548dfe5c6msh388cd314a63a60fp10805bjsn83e6c1254b86"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}
