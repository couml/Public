from __future__ import annotations

from typing import Any


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", error_code: Optional[str] = None):
        super().__init__(status_code=404, detail=detail, error_code=error_code)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request", error_code: Optional[str] = None):
        super().__init__(status_code=400, detail=detail, error_code=error_code)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Unauthorized", error_code: Optional[str] = None):
        super().__init__(status_code=401, detail=detail, error_code=error_code)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden", error_code: Optional[str] = None):
        super().__init__(status_code=403, detail=detail, error_code=error_code)


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict", error_code: Optional[str] = None):
        super().__init__(status_code=409, detail=detail, error_code=error_code)
