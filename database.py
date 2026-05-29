from __future__ import annotations
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, JSON, select
from config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

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

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

async def save_search(session: AsyncSession, query_type: str, query_value: str) -> Search:
    search = Search(query_type=query_type, query_value=query_value, status='running')
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
