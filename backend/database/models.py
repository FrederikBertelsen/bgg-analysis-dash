from datetime import timedelta, datetime
from typing import cast, Optional, Any, Dict

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
    Boolean,
    JSON,
)
import enum

from backend.utils import parse_datetime, format_datetime

Base = declarative_base()


class BoardGame(Base):
    __tablename__ = "boardgames"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScrapeTask(Base):
    __tablename__ = "scrape_tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)

    class ScrapeStatus(enum.Enum):
        none = "none"
        pending = "pending"
        running = "running"
        completed = "completed"
        failed = "failed"

    status = Column(
        SAEnum(ScrapeStatus, name="scrape_status", native_enum=False),
        nullable=False,
        default=ScrapeStatus.none,
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


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True)
    task_id = Column(
        "task_id_fk",
        Integer,
        ForeignKey("scrape_tasks.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    line_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    text = Column(Text, nullable=False)
    task = relationship("ScrapeTask", back_populates="logs")


class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True)
    source_table = Column(String(255), nullable=False, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    scrape_task_id = Column(
        Integer,
        ForeignKey("scrape_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, nullable=False, default=False, server_default="false")
    processor_version = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CleanData(Base):
    __tablename__ = "clean_data"

    id = Column(Integer, primary_key=True)
    raw_id = Column(
        "raw_id_fk",
        Integer,
        ForeignKey("raw_data.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    source_table = Column(String(255), nullable=False, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    scrape_task_id = Column(
        Integer,
        ForeignKey("scrape_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload = Column(JSON, nullable=False)
    processor_version = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Composite index for fast retrieval of latest lines per task.
Index("ix_scrape_logs_task_line_no", ScrapeLog.task_id, ScrapeLog.line_no.desc())

# Composite index for fast retrieval of clean data by source table and id, ordered by creation time.
Index(
    "ix_clean_data_source_table_source_id_created_at",
    CleanData.source_table,
    CleanData.source_id,
    CleanData.created_at.desc(),
)
