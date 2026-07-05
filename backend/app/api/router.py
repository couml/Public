from __future__ import annotations

from fastapi import APIRouter

from .auth import router as auth_router
from .devices import router as devices_router
from .files import router as files_router
from .print_jobs import router as print_router
from .drivers import router as drivers_router
from .diagnosis import router as diagnosis_router
from .documents import router as documents_router
from .admin import router as admin_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(devices_router, tags=["Devices"])
api_router.include_router(files_router, tags=["Files"])
api_router.include_router(print_router, tags=["Print Jobs"])
api_router.include_router(drivers_router, tags=["Drivers"])
api_router.include_router(diagnosis_router, tags=["Diagnosis"])
api_router.include_router(documents_router, tags=["Documents"])
api_router.include_router(admin_router, tags=["Admin"])
