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


class ScrapeLog(Base):
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


# Composite index for fast retrieval of latest lines per task.
Index("ix_scrape_logs_task_line_no", ScrapeLog.task_id_fk, ScrapeLog.line_no.desc())
