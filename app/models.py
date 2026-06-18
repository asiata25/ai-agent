from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = WORKSPACE_ROOT / "database.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


class VisualizationHistory(Base):
    """Track visualization requests and their outcomes."""

    __tablename__ = "visualization_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    csv_file = Column(String)
    chart_type = Column(String, nullable=True)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_visualization_history(
    *,
    session_id: str,
    csv_file: str,
    chart_type: str | None = None,
) -> VisualizationHistory:
    """Create a pending visualization history row."""
    async with async_session() as session:
        history = VisualizationHistory(
            session_id=session_id,
            csv_file=csv_file,
            chart_type=chart_type,
            status="pending",
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)
        return history


async def finish_visualization_history(
    *,
    history_id: int,
    status: str,
    chart_type: str | None = None,
    error_message: str | None = None,
) -> VisualizationHistory | None:
    """Mark a visualization history row as completed."""
    async with async_session() as session:
        history = await session.get(VisualizationHistory, history_id)
        if history is None:
            return None

        history.status = status
        history.chart_type = chart_type or history.chart_type
        history.error_message = error_message
        history.completed_at = datetime.utcnow()
        await session.commit()
        await session.refresh(history)
        return history


async def list_visualization_history(limit: int = 20) -> list[VisualizationHistory]:
    """Return recent visualization history rows."""
    async with async_session() as session:
        result = await session.scalars(
            select(VisualizationHistory)
            .order_by(VisualizationHistory.created_at.desc())
            .limit(limit)
        )
        return list(result)
