from __future__ import annotations

from typing import Optional
import uuid

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    existing = await db.execute(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=409, detail="Username or email already exists"
        )

    user = User(
        username=username,
        email=email,
        hashed_password=pwd_context.hash(password),
        full_name=full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password"
        )
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
