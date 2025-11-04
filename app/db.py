from typing import List

# In-memory database simulation
db_users = {}
db_accounts = {}
db_blacklist = {}
db_integration_pending = {}
db_integration = {}


def get_user(username: str):
    return db_users.get(username)


def calculate_median(data: List[int]):
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 0:
        return 0
    if n % 2 == 1:
        return sorted_data[n // 2]
    else:
        return (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2


def save_to_db(results, username: str):
    """
    Save processed user data into the database.
    Args:
        results: List of tuples containing (username, followers_count, avg_views, reels_with_10000_views).
        username: The name of the user's table to insert data into.
    """
    if not results:
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
