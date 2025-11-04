from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder from repo root
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
try:
    from .api.routes import router as api_router
    app.include_router(api_router)
except Exception:
    # during initial import (before routes exist) ignore
    pass
