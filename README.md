# Instagram Dashboard API

FastAPI-based dashboard for analyzing Instagram accounts with PostgreSQL database.

## ⚠️ Important: Python Version Compatibility

**Current status:** The project uses Python 3.14, but some dependencies don't support it yet:
- `asyncpg` (PostgreSQL async driver)
- `pydantic_core` (Pydantic v2)

**Recommended:** Use Python 3.11 or 3.12 for full functionality.

See [SETUP.md](SETUP.md) for detailed PostgreSQL setup instructions.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the quick start script
./quickstart.sh
```

This script will:
- ✅ Check Python version (3.11 or 3.12)
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Start PostgreSQL in Docker
- ✅ Setup and run database migrations
- ✅ Provide next steps

### Option 2: Manual Setup

### 1. Setup Database (Docker - Recommended)

```bash
# Start PostgreSQL 17 in Docker
docker-compose up -d

# Check status
docker-compose ps
```

Alternative: See [SETUP.md](SETUP.md) for other installation methods.

### 2. Install Dependencies

```bash
# Recommended: Use Python 3.11 or 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
alembic init alembic  # If not done already
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### 4. Run Application

```bash
# Debug mode (no real API calls, uses mock data)
python main.py --debug

# Production mode (requires Instagram RapidAPI key)
python main.py
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
├── SETUP.md                    # PostgreSQL setup guide
├── app/
│   ├── __init__.py            # FastAPI app with lifespan events
│   ├── models.py              # Pydantic models
│   ├── database.py            # SQLAlchemy async engine & sessions
│   ├── db_models.py           # SQLAlchemy ORM models
│   ├── crud.py                # Database CRUD operations
│   ├── utils.py               # Utility functions (calculate_median)
│   ├── security.py            # Auth & JWT token handling
│   ├── core/
│   │   └── config.py          # Configuration (DEBUG_MODE, DATABASE_URL)
│   ├── services/
│   │   ├── instagram.py       # Instagram API service (debug-aware)
│   │   └── mock_instagram.py  # Mock data generators for debug mode
│   └── api/
│       ├── auth.py            # Authentication endpoints
│       ├── accounts.py        # Account management
│       ├── integration.py     # Integration management
│       ├── blacklist.py       # Blacklist management
│       └── frontend.py        # HTML serving
├── static/                     # Static files (CSS, JS)
├── templates/                  # Jinja2 templates
└── alembic/                    # Database migrations
```

## Database Schema

The application uses PostgreSQL with the following tables:

- **users** - User authentication
- **instagram_accounts** - Tracked Instagram accounts
- **blacklist_accounts** - Blacklisted accounts
- **integration_pending** - Accounts awaiting integration
- **integrations** - Integrated accounts with reels data (JSON)

See `app/db_models.py` for complete schema definitions.

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

The application uses a modern async architecture with:
- **PostgreSQL Database**: Persistent storage with SQLAlchemy async ORM
- **Debug mode support**: Mock data for development without API quota consumption
- **JWT authentication**: Secure token-based authentication
- **Async/await**: Full async support with asyncpg driver
- **Alembic migrations**: Database schema version control
- **Modular structure**: Clean separation of concerns (API, services, CRUD, models)

### Development Workflow

1. **Make code changes** in `app/` directory
2. **Create migration** if database schema changed: `alembic revision --autogenerate -m "Description"`
3. **Apply migration**: `alembic upgrade head`
4. **Test in debug mode**: `python main.py --debug`
5. **Test with real API**: `python main.py` (requires RapidAPI key in config)

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql+asyncpg://postgres:postgres@localhost:5432/instagram_dashboard`)
- Configure other settings in `app/core/config.py`

### Useful Commands (Makefile)

```bash
make help              # Show all available commands
make setup             # Initial setup (run once)
make start             # Start PostgreSQL
make stop              # Stop PostgreSQL
make logs              # View database logs
make run               # Run application
make run-debug         # Run in debug mode
make migrate-create    # Create new migration
make migrate-up        # Apply migrations
make db-shell          # Open PostgreSQL shell
make db-backup         # Backup database
```

See `Makefile` for all available commands.
