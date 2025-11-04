from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.api import auth, accounts, integration, blacklist, frontend


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    from app.database import init_db, close_db
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder from repo root
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include all API routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(integration.router)
app.include_router(blacklist.router)
app.include_router(frontend.router)
