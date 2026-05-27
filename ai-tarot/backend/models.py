"""
SQLAlchemy ORM models for AI Tarot.
All models use async-compatible SQLAlchemy 2.x declarative style.
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    avatar: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    daily_free_count: Mapped[int] = mapped_column(Integer, default=3)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    vip_expire: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Divination(Base):
    __tablename__ = "divinations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    spread_type: Mapped[str] = mapped_column(String(64), nullable=False)
    cards_json: Mapped[str] = mapped_column(JSON, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    persona: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # in fen (cents)
    product_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
