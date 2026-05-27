"""
AI Tarot - FastAPI Backend Application
A tarot divination mini-program with multiple persona styles.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import divination, user, payment

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="AI Tarot",
    description="AI-powered tarot divination with multiple persona styles",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for WeChat mini-program / web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(divination.router)
app.include_router(user.router)
app.include_router(payment.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "ai-tarot"}


# Mount static files for frontend (must be last)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
