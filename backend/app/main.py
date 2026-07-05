from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed if DB is empty
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            print("Database empty, seeding...")
            from scripts.seed import seed
            await seed()
            print("Seed complete.")

    print("Redis not available, using mock mode.")
    print("MinIO not available, using mock mode.")

    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME + " API",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Parse CORS origins from settings, fallback to allow all in production
_cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if not _cors_origins or settings.DEBUG:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.router import api_router
app.include_router(api_router)

# Mount WebSocket endpoint
from app.websocket.device_ws import router as ws_router
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"message": "Smart Printer Platform API", "version": "1.0.0"}
