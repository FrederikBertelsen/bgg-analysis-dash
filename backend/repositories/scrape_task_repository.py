from typing import List, Optional
import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.database.schemas import ScrapeStatus, ScrapeTaskCreate, ScrapeTaskOut

from .base_repository import BaseRepository
from ..database import models


class ScrapeTaskRepository(BaseRepository):
    @staticmethod
    def create_task(session: Session, create: ScrapeTaskCreate) -> ScrapeTaskOut:
        task = models.ScrapeTask(
            name=create.name, status=create.status, progress=(create.progress or 0.0)
        )
        session.add(task)
        session.flush()
        session.refresh(task)
        return ScrapeTaskOut.model_validate(task)

    @staticmethod
    def get_by_id(session: Session, task_id: int) -> Optional[ScrapeTaskOut]:
        obj = (
            session.execute(
                select(models.ScrapeTask).where(models.ScrapeTask.id == task_id)
            )
            .scalars()
            .first()
        )
        return ScrapeTaskOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def get_by_status(session: Session, status: ScrapeStatus) -> List[ScrapeTaskOut]:
        objs = list(
            session.execute(
                select(models.ScrapeTask).where(
                    models.ScrapeTask.status == status.value
                )
            )
            .scalars()
            .all()
        )
        return [ScrapeTaskOut.model_validate(o) for o in objs]

    @staticmethod
    def get_latest_completed_task_by_name(
        session: Session, name: Optional[str] = None
    ) -> Optional[ScrapeTaskOut]:
        stmt = select(models.ScrapeTask).where(
            models.ScrapeTask.status == ScrapeStatus.completed.value
        )
        if name is not None:
            stmt = stmt.where(models.ScrapeTask.name == name)

        obj = (
            session.execute(stmt.order_by(models.ScrapeTask.created_at.desc()))
            .scalars()
            .first()
        )

        return ScrapeTaskOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def get_all_tasks(session: Session) -> List[ScrapeTaskOut]:
        objs = list(session.execute(select(models.ScrapeTask)).scalars().all())
        return [ScrapeTaskOut.model_validate(o) for o in objs]

    @staticmethod
    def update_progress(
        session: Session,
        task_id: int,
        progress: Optional[float] = None,
        status: Optional[ScrapeStatus] = None,
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
            values["status"] = status.value
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
