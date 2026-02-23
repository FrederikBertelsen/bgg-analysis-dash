from datetime import timedelta, datetime
from typing import cast

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    func,
    ForeignKey,
    Index,
    Enum as SAEnum,
)
import enum

from backend.utils import estimate_eta

Base = declarative_base()


def _format_datetime(dt):
    """Return a human-readable datetime string or None.

    Falls back to ISO format on unexpected errors.
    """
    if dt is None:
        return None
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return getattr(dt, "isoformat", lambda: None)()


class ModelBase(Base):
    __abstract__ = True

    def to_dict(self):
        raise NotImplementedError("Subclasses must implement to_dict() method")


class BoardGame(ModelBase):
    __tablename__ = "boardgames"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "url": self.url}


class ScrapeTask(ModelBase):
    __tablename__ = "scrape_tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)

    class ScrapeStatus(enum.Enum):
        pending = "pending"
        running = "running"
        completed = "completed"
        failed = "failed"

    status = Column(
        SAEnum(ScrapeStatus, name="scrape_status", native_enum=False),
        nullable=False,
        default=ScrapeStatus.pending,
    )
    progress = Column(Float, nullable=False, default=0.0)
    current_page = Column(Integer, nullable=True)
    items_processed = Column(Integer, nullable=True)
    # Per-task counter for log line numbering. Use atomic UPDATE...RETURNING to increment.
    last_line_no = Column(Integer, nullable=False, server_default="0")
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_update = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # relationship to logs; cascade deletes so logs are removed when a task is deleted
    logs = relationship(
        "ScrapeLog",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        # Safely determine runtime status using a plain Python bool to avoid SQLAlchemy ColumnElement in conditionals
        status = getattr(self, "status", None)
        is_running = False
        if isinstance(status, self.ScrapeStatus):
            is_running = status == self.ScrapeStatus.running

        return {
            "id": self.id,
            "name": self.name,
            "status": (
                status.value
                if isinstance(status, self.ScrapeStatus)
                else getattr(status, "value", status)
            ),
            "progress": self.progress,
            "current_page": self.current_page,
            "items_processed": self.items_processed,
            "message": self.message,
            "created_at": _format_datetime(self.created_at),
            "last_update": _format_datetime(self.last_update),
            "eta": (
                estimate_eta(
                    cast(float, self.progress),
                    cast(datetime, self.last_update),
                    cast(datetime, self.created_at),
                )
                if is_running
                else None
            ),
        }


class ScrapeLog(ModelBase):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True)
    task_id_fk = Column(
        Integer,
        ForeignKey("scrape_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    text = Column(Text, nullable=False)
    task = relationship("ScrapeTask", back_populates="logs")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id_fk": self.task_id_fk,
            "line_no": self.line_no,
            "created_at": _format_datetime(self.created_at),
            "text": self.text,
        }


# Composite index for fast retrieval of latest lines per task.
Index("ix_scrape_logs_task_line_no", ScrapeLog.task_id_fk, ScrapeLog.line_no.desc())
