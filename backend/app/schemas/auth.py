from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.common import ORMModel
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(ORMModel):
    """用户注册请求"""

    username: str = Field(min_length=3, max_length=64, description="用户名")
    email: EmailStr = Field(description="电子邮箱")
    password: str = Field(min_length=8, description="密码，最少8位")
    full_name: Optional[str] = Field(default=None, max_length=128, description="全名")


class LoginRequest(ORMModel):
    """用户登录请求"""

    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")


class TokenResponse(ORMModel):
    """认证令牌响应"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class RefreshRequest(ORMModel):
    """刷新令牌请求"""

    refresh_token: str = Field(description="刷新令牌")
