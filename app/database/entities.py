from collections.abc import AsyncGenerator
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, DateTime, Text,
    ForeignKey, Enum
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, relationship

DATABASE_URL = (
    "postgresql+asyncpg://neondb_owner:npg_hPEAGUrD0tM7"
    "@ep-weathered-fire-ad168ndy-pooler.c-2.us-east-1.aws.neon.tech/neondb"
)
# postgresql://neondb_owner:npg_hPEAGUrD0tM7@ep-weathered-fire-ad168ndy-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Base class
class Base(DeclarativeBase):
    pass


# ----------------------------------
# Repositories Table
# ----------------------------------
class Repositories(Base):
    __tablename__ = "repositories"

    id = Column(
        String(36),  # SQLite safe
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )

    # Owner user
    user_id = Column(
        String(36),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(String(255), nullable=False)
    description = Column(Text)
    github_url = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chats = relationship(
        "ChatHistory",
        back_populates="repo",
        cascade="all, delete-orphan",
    )
    user = relationship(
        "userProfiles",
        back_populates="repositories",
    )


# ----------------------------------
# Enum for Chat Role
# ----------------------------------
class ChatRole(str, PyEnum):
    user = "user"
    ai = "ai"


# ----------------------------------
# Chat History Table
# ----------------------------------
class ChatHistory(Base):
    __tablename__ = "chats"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    user_id = Column(
        String(36),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False
    )

    repo_id = Column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(Enum(ChatRole), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repo = relationship("Repositories", back_populates="chats")
    user = relationship("userProfiles", back_populates="chats")


class userProfiles(Base):
    __tablename__ = "user_profiles"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )

    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repositories = relationship(
        "Repositories",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chats = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# ----------------------------------
# Engine and Session
# ----------------------------------
engine = create_async_engine(DATABASE_URL, echo=False,connect_args={"ssl": "require"})
async_engine_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_engine_maker() as session:
        yield session
