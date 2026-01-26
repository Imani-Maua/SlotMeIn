from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Boolean, Numeric, Date, Time, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column



class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    firstname: Mapped[str] = mapped_column(String(50))
    lastname: Mapped[str] = mapped_column(String(50))
    user_role: Mapped[str] = mapped_column(String(50))
    pwd_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

class AccessToken(Base):
    __tablename__ = "access_token"

    id:Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    jti:Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[Optional[date]] = mapped_column(Date)
    used_at: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[Optional[date]] = mapped_column(Date)

class InviteToken(Base):
    __tablename__ = "invite_token"

    id:Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    jti:Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[Optional[date]] = mapped_column(Date)
    used_at: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[Optional[date]] = mapped_column(Date)