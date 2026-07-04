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

    # Try to connect Redis (skip if unavailable)
    try:
        from app.utils.redis_client import get_redis
        get_redis().ping()
        print("Redis connected.")
    except Exception:
        print("Redis not available, using mock mode.")

    # Try to connect MinIO (skip if unavailable)
    try:
        from app.utils.minio_client import minio_client
        minio_client.ensure_bucket(settings.MINIO_BUCKET)
        print("MinIO connected.")
    except Exception:
        print("MinIO not available, using mock mode.")

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME + " API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
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
