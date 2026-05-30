from __future__ import annotations
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, JSON, Boolean, Integer, ForeignKey, select
from config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(200))
    totp_secret: Mapped[str] = mapped_column(String(32), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Search(Base):
    __tablename__ = 'searches'

    id: Mapped[int] = mapped_column(primary_key=True)
    query_type: Mapped[str] = mapped_column(String(20))
    query_value: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    completed_at = mapped_column(DateTime, nullable=True)
    results = mapped_column(JSON, nullable=True)
    ai_analysis = mapped_column(Text, nullable=True)
    report_path = mapped_column(String(500), nullable=True)
    error = mapped_column(Text, nullable=True)
    user_id = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default='public')

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

async def save_search(session: AsyncSession, query_type: str, query_value: str, user_id: int = None, visibility: str = 'public') -> Search:
    search = Search(
        query_type=query_type, query_value=query_value,
        status='running', user_id=user_id, visibility=visibility
    )
    session.add(search)
    await session.commit()
    await session.refresh(search)
    return search

async def update_search(session: AsyncSession, search_id: int, **kwargs):
    search = await session.get(Search, search_id)
    if search:
        for k, v in kwargs.items():
            setattr(search, k, v)
        await session.commit()

async def get_user_by_dni(session: AsyncSession, dni: str) -> User | None:
    result = await session.execute(select(User).where(User.dni == dni))
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)

async def create_user(session: AsyncSession, dni: str, display_name: str, password_hash: str) -> User:
    user = User(dni=dni, display_name=display_name, password_hash=password_hash)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(User))
    return len(result.scalars().all())
