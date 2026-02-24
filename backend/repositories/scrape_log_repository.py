from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.database import models, schemas
from backend.database.schemas import ScrapeLogLineOut
from .base_repository import BaseRepository


class ScrapeLogRepository(BaseRepository):
    @staticmethod
    def append_line(session: Session, task_id: int, text: str) -> ScrapeLogLineOut:
        # Atomically increment per-task counter and get the next line_no.
        # Uses UPDATE ... RETURNING to avoid races and avoid scanning the logs table.
        inc_stmt = (
            update(models.ScrapeTask)
            .where(models.ScrapeTask.id == task_id)
            .values(last_line_no=models.ScrapeTask.last_line_no + 1)
            .returning(models.ScrapeTask.last_line_no)
        )
        result = session.execute(inc_stmt)
        next_line_no = int(result.scalar_one())

        log = models.ScrapeLog(task_id=task_id, line_no=next_line_no, text=text)
        session.add(log)
        session.flush()
        session.refresh(log)
        return ScrapeLogLineOut.model_validate(log)

    @staticmethod
    def get_recent_logs(
        session: Session, task_id: int, limit: int = 200
    ) -> List[ScrapeLogLineOut]:
        stmt = (
            select(models.ScrapeLog)
            .where(models.ScrapeLog.task_id == task_id)
            .order_by(models.ScrapeLog.line_no.desc())
            .limit(limit)
        )
        rows = list(session.execute(stmt).scalars().all())
        # Query used DESC+LIMIT for efficiency; reverse so callers get oldest->newest order.
        rows = list(reversed(rows))
        return [ScrapeLogLineOut.model_validate(r) for r in rows]
