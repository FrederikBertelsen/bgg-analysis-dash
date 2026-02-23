from typing import Iterable, List, Optional
from sqlalchemy.exc import OperationalError
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
import pandas as pd

from . import models
from .schemas import BoardGameIn


class BaseRepository:
    # thin helper placeholder for retries / common behavior
    retry_errors = (OperationalError,)


class BoardGameRepository(BaseRepository):
    @staticmethod
    def upsert(session: Session, boardgame: BoardGameIn) -> None:
        """Upsert a single boardgame using Postgres ON CONFLICT."""
        stmt = pg_insert(models.BoardGame).values(
            id=boardgame.id, name=boardgame.name, url=boardgame.url
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.BoardGame.id],
            set_={"name": stmt.excluded.name, "url": stmt.excluded.url},
        )
        session.execute(stmt)

    @staticmethod
    def bulk_upsert(session: Session, boardgames: Iterable[BoardGameIn]) -> None:
        boardgame_dicts = [bg.model_dump() for bg in boardgames]
        if not boardgame_dicts:
            return

        stmt = pg_insert(models.BoardGame).values(boardgame_dicts)
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.BoardGame.id],
            set_={"name": stmt.excluded.name, "url": stmt.excluded.url},
        )
        session.execute(stmt)

    @staticmethod
    def get(session: Session, boardgame_id: int) -> Optional[models.BoardGame]:
        return (
            session.execute(
                select(models.BoardGame).where(models.BoardGame.id == boardgame_id)
            )
            .scalars()
            .first()
        )

    @staticmethod
    def get_some(
        session: Session, skip: int = 0, take: int = 100
    ) -> List[models.BoardGame]:
        return list(
            session.execute(select(models.BoardGame).offset(skip).limit(take))
            .scalars()
            .all()
        )

    @staticmethod
    def get_all(session: Session) -> List[models.BoardGame]:
        return list(session.execute(select(models.BoardGame)).scalars().all())

    @staticmethod
    def get_some_as_dataframe(
        session: Session, skip: int = 0, take: int = 100
    ) -> pd.DataFrame:
        boardgames = BoardGameRepository.get_some(session, skip, take)
        boardgame_dicts = [boardgame.to_dict() for boardgame in boardgames]
        return pd.DataFrame(boardgame_dicts)

    @staticmethod
    def get_all_as_dataframe(session: Session):

        boardgames = BoardGameRepository.get_all(session)
        boardgame_dicts = [boardgame.to_dict() for boardgame in boardgames]
        return pd.DataFrame(boardgame_dicts)


class ScrapeTaskRepository(BaseRepository):
    @staticmethod
    def create_task(
        session: Session, name: str, status: str = "pending"
    ) -> models.ScrapeTask:
        task = models.ScrapeTask(name=name, status=status, progress=0.0)
        session.add(task)
        session.flush()
        return task

    @staticmethod
    def get_by_id(session: Session, task_id: int) -> Optional[models.ScrapeTask]:
        return (
            session.execute(
                select(models.ScrapeTask).where(models.ScrapeTask.id == task_id)
            )
            .scalars()
            .first()
        )

    @staticmethod
    def update_progress(
        session: Session,
        task_id: int,
        progress: Optional[float] = None,
        status: Optional[str] = None,
        current_page: Optional[int] = None,
        items_processed: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update selected fields for a ScrapeTask. Only provided fields are written.

        Use explicit parameters for IDE autocomplete and static checks.
        """
        values = {}
        if progress is not None:
            values["progress"] = progress
        if status is not None:
            values["status"] = status
        if current_page is not None:
            values["current_page"] = current_page
        if items_processed is not None:
            values["items_processed"] = items_processed
        if message is not None:
            values["message"] = message

        if not values:
            return

        stmt = (
            update(models.ScrapeTask)
            .where(models.ScrapeTask.id == task_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        session.execute(stmt)


class ScrapeLogRepository(BaseRepository):
    @staticmethod
    def append_line(session: Session, task_id: int, text: str) -> None:
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

        log = models.ScrapeLog(task_id_fk=task_id, line_no=next_line_no, text=text)
        session.add(log)

    @staticmethod
    def get_recent_logs(
        session: Session, task_id: int, limit: int = 200
    ) -> List[models.ScrapeLog]:
        stmt = (
            select(models.ScrapeLog)
            .where(models.ScrapeLog.task_id_fk == task_id)
            .order_by(models.ScrapeLog.line_no.desc())
            .limit(limit)
        )
        rows = list(session.execute(stmt).scalars().all())
        # Query used DESC+LIMIT for efficiency; reverse so callers get oldest->newest order.
        return list(reversed(rows))
