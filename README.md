# Instagram Dashboard API

FastAPI-based dashboard for analyzing Instagram accounts.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

### Normal Mode (with real API calls)

```bash
python3 main.py
```

Or with custom host/port:

```bash
python3 main.py --host 127.0.0.1 --port 8080
```

### Debug Mode (with mock data)

Run the application with `--debug` flag to use mock data instead of real Instagram API calls. This is useful for:
- Development without consuming API quota
- Testing without network connectivity
- Running tests without external dependencies

```bash
python3 main.py --debug
```

When debug mode is enabled:
- All Instagram API calls are replaced with mock responses
- Random but realistic data is generated
- No network calls are made to RapidAPI
- Console shows `🔧 DEBUG MODE ENABLED` message

### Command-line Options

```
usage: main.py [-h] [--debug] [--host HOST] [--port PORT]

Instagram Dashboard API

options:
  -h, --help   show this help message and exit
  --debug      Run in debug mode with mock API responses (no real API calls)
  --host HOST  Host to bind to (default: 0.0.0.0)
  --port PORT  Port to bind to (default: 8000)
```

## Project Structure

```
.
├── main.py                     # Entry point with CLI args
├── requirements.txt            # Python dependencies
├── app/
│   ├── __init__.py            # FastAPI app initialization
│   ├── models.py              # Pydantic models
│   ├── db.py                  # In-memory database
│   ├── security.py            # Auth & security
│   ├── core/
│   │   └── config.py          # Configuration (includes DEBUG_MODE)
│   ├── services/
│   │   ├── instagram.py       # Instagram API service (debug-aware)
│   │   └── mock_instagram.py  # Mock data generators
│   └── api/
│       ├── auth.py            # Authentication endpoints
│       ├── accounts.py        # Account management
│       ├── integration.py     # Integration management
│       ├── blacklist.py       # Blacklist management
│       └── frontend.py        # HTML serving
├── static/                     # Static files (CSS, JS)
└── templates/                  # Jinja2 templates
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /token` - Login and get access token

### Accounts
- `GET /accounts` - List user's accounts
- `POST /accounts` - Add new account
- `DELETE /accounts/{username}` - Delete account
- `POST /accounts/analyze_followings` - Analyze followings

### Integration
- `GET /integration_pending` - List pending integrations
- `GET /integration` - List active integrations
- `POST /move_to_integration_pending/{username}` - Move to pending
- `POST /move_to_integration/{username}` - Move to active
- `POST /integration/{username}/reels` - Add reels to integration
- `POST /update_reels_data` - Update reels metrics
- `POST /fetch_reels_data` - Fetch single reel data

### Blacklist
- `GET /blacklist` - List blacklisted accounts
- `POST /blacklist` - Add to blacklist
- `DELETE /blacklist/{username}` - Remove from blacklist
- `POST /blacklist/multiple` - Add multiple to blacklist

## Development

The application uses a modular structure with:
- **Debug mode support**: All API calls can be mocked for development
- **In-memory database**: Data is stored in memory (reset on restart)
- **JWT authentication**: Secure token-based auth
- **Async/await**: Full async support for Instagram API calls
