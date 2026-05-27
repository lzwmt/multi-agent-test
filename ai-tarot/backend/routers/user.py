"""
User router - handles user authentication and profile.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/user", tags=["user"])


class LoginRequest(BaseModel):
    """Login via WeChat code or anonymous access."""
    code: str = ""  # WeChat login code, empty for anonymous
    nickname: str = "神秘访客"


class LoginResponse(BaseModel):
    token: str
    user_id: int
    nickname: str
    daily_free_count: int
    is_vip: bool


class UserProfile(BaseModel):
    id: int
    nickname: str
    avatar: str
    daily_free_count: int
    is_vip: bool
    created_at: str


# Simple token store (in production, use JWT)
_tokens: dict[str, int] = {}


def _make_token(user_id: int) -> str:
    token = uuid.uuid4().hex
    _tokens[token] = user_id
    return token


async def get_current_user_id(
    authorization: str = Header(default=""),
) -> int | None:
    """Extract user ID from Authorization header. Returns None if invalid."""
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        return _tokens.get(token)
    return None


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login or create anonymous user."""
    # For now, create anonymous user with unique openid
    openid = f"anon_{uuid.uuid4().hex[:16]}" if not req.code else f"wx_{req.code}"

    # Check if user exists (by openid for WeChat, always create new for anon)
    user = None
    if req.code:
        stmt = select(User).where(User.openid == openid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        user = User(
            openid=openid,
            nickname=req.nickname,
            avatar="",
            daily_free_count=3,
            is_vip=False,
        )
        db.add(user)
        await db.flush()

    token = _make_token(user.id)

    return LoginResponse(
        token=token,
        user_id=user.id,
        nickname=user.nickname,
        daily_free_count=user.daily_free_count,
        is_vip=user.is_vip,
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile."""
    user_id = await get_current_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserProfile(
        id=user.id,
        nickname=user.nickname,
        avatar=user.avatar,
        daily_free_count=user.daily_free_count,
        is_vip=user.is_vip,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )
