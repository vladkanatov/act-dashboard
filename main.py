import asyncio
import aiohttp
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
import sqlite3
from functools import wraps


app = Flask(__name__)
app.secret_key = "supersecretkey"


# RapidAPI credentials
RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
RAPIDAPI_KEY = "d4ebe642d8mshb00f6ef71d7bdbfp1cd730jsn0b95f7109de5"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

# Database setup
def init_db(username: str):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS accounts_{username} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    followers_count INTEGER,
                    avg_views INTEGER,
                    reels_with_10000_views INTEGER)''')
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'username' not in session:
        return render_template('index.html', accounts=[])
    
    username = session['username']
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM accounts_{username}")
    accounts = c.fetchall()
    conn.close()
    
    return render_template('index.html', accounts=accounts, username=username, logged_in=False)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    
    init_db(username)
    
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        return jsonify({'error': 'User already exists!'}), 400
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    c.execute(f"CREATE TABLE IF NOT EXISTS accounts_{username} (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, followers_count INTEGER, avg_views INTEGER, reels_with_10000_views INTEGER)")
    conn.commit()
    conn.close()
    return jsonify({'message': 'User registered successfully!'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'Invalid credentials!'}), 401
    
    session['username'] = username
    return jsonify({'message': 'Login successful'}), 200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/get_accounts', methods=['GET'])
@login_required
def get_accounts():
    username = session['username']
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM accounts_{username}")
    accounts = c.fetchall()
    conn.close()
    
    return jsonify(accounts)

@app.route('/add_account', methods=['POST'])
def add_account():
    username = request.json.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    

    profile_url = f"https://{RAPIDAPI_HOST}/v1/info"
    profile_response = requests.get(profile_url, headers=HEADERS, params={"username_or_id_or_url": username})
    
    data = profile_response.json()['data']
    followers_count = data['follower_count']
    
    reels = []
    pagination_token = None
    for _ in range(10):
        reels_url = f"https://{RAPIDAPI_HOST}/v1.2/reels"
        params = {"username_or_id_or_url": username}
        if pagination_token:
            params["pagination_token"] = pagination_token

        reels_response = requests.get(reels_url, headers=HEADERS, params=params)
        if reels_response.status_code != 200:
            break

        reels_data = reels_response.json()
        reels.extend(reels_data['data']['items'])
        pagination_token = reels_data.get('pagination_token')
        if not pagination_token:
            break

    if not reels:
        return jsonify({"error": "No reels found for this account"}), 400
    
    
    views = [reel['play_count'] for reel in reels]
    avg_views = int(sum(views) / len(views))
    reels_with_10000_views = sum(1 for view in views if view > 10000)

    # Save to database
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute(f'''INSERT OR IGNORE INTO accounts_{session['username']} (username, followers_count, avg_views, reels_with_10000_views)
                 VALUES (?, ?, ?, ?)''', (username, followers_count, avg_views, reels_with_10000_views))
    conn.commit()
    conn.close()
    return jsonify({"message": "Account added successfully"})

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.json.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM accounts_{session['username']} WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Account deleted successfully"})

@app.route('/clear', methods=['GET'])
def clear():
    session.clear()
    return jsonify({"message": "Session cleared"}), 200

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

async def process_followings(username):
    async with aiohttp.ClientSession() as ses:
        
        # Получаем список followings
        followings_data = await fetch_followings(ses, username)
        followings = [item['id'] for item in followings_data['data']['items']]

        tasks = []
        for user_id in followings:
            tasks.append(process_user(ses, user_id))
        results = await asyncio.gather(*tasks)
        
        table_name = f"accounts_{session["username"]}"
        
        save_to_db(results, table_name)

async def process_user(session, user_id):
    # Получаем профиль пользователя
    profile_data = await fetch_profile(session, user_id)
    username = profile_data['data']['username']
    followers_count = profile_data['data']['follower_count']

    # Получаем рилсы
    reels = await fetch_reels(session, user_id)
    views = [reel['play_count'] for reel in reels if 'play_count' in reel]
    avg_views = int(sum(views) / len(views)) if views else 0
    reels_with_10000_views = sum(1 for view in views if view > 10000)

    # Проверяем критерии
    if avg_views < 3000 or reels_with_10000_views < 3:
        return None

    return (username, followers_count, avg_views, reels_with_10000_views)

def save_to_db(results, table_name):
    """
    Save processed user data into the database.
    Args:
        results: List of tuples containing (username, followers_count, avg_views, reels_with_10000_views).
        table_name: The name of the user's table to insert data into.
    """
    if not results:
        print("No valid results to save.")
        return

    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()

    for result in results:
        if result:  # Ensure the result is not None
            try:
                c.execute(f'''
                    INSERT OR IGNORE INTO {table_name} 
                    (username, followers_count, avg_views, reels_with_10000_views)
                    VALUES (?, ?, ?, ?)''', result)
            except sqlite3.Error as e:
                print(f"Error saving data to database: {e}")

    conn.commit()
    conn.close()


@app.route('/analyze_subscriptions', methods=['POST'])
def analyze_subscriptions():
    username = request.json.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    asyncio.run(process_followings(username))
    return jsonify({"message": "Accounts analyzed successfully"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=False)

