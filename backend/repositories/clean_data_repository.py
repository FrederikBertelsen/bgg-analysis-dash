from typing import Any, List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from .base_repository import BaseRepository
from ..database import models, schemas
from ..database.schemas import CleanDataIn, CleanDataOut


class CleanDataRepository(BaseRepository):
    @staticmethod
    def create(
        session: Session, clean_in: CleanDataIn, raw_id: Optional[int] = None
    ) -> CleanDataOut:
        clean = models.CleanData(
            raw_id=raw_id,
            source_table=clean_in.source_table,
            source_id=clean_in.source_id,
            scrape_task_id=clean_in.scrape_task_id,
            payload=clean_in.payload,
            processor_version=clean_in.processor_version,
        )
        session.add(clean)
        session.flush()
        session.refresh(clean)
        return CleanDataOut.model_validate(clean)

    @staticmethod
    def get_by_id(session: Session, clean_id: int) -> Optional[CleanDataOut]:
        obj = session.get(models.CleanData, clean_id)
        return CleanDataOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def get_by_source_id_and_table(
        session: Session, source_table: str, source_id: int
    ) -> Optional[CleanDataOut]:
        stmt = (
            select(models.CleanData)
            .where(
                (models.CleanData.source_table == source_table)
                & (models.CleanData.source_id == source_id)
            )
            .order_by(models.CleanData.created_at.desc())
            .limit(1)
        )
        obj = session.execute(stmt).scalars().first()
        return CleanDataOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def get_by_raw_id(session: Session, raw_id: int) -> List[CleanDataOut]:
        stmt = select(models.CleanData).where(models.CleanData.raw_id == raw_id)
        objs = list(session.execute(stmt).scalars().all())
        return [CleanDataOut.model_validate(o) for o in objs]

    @staticmethod
    def get_by_scrape_task_id(
        session: Session, scrape_task_id: int
    ) -> List[CleanDataOut]:
        stmt = select(models.CleanData).where(
            models.CleanData.scrape_task_id == scrape_task_id
        )
        objs = list(session.execute(stmt).scalars().all())
        return [CleanDataOut.model_validate(o) for o in objs]

    @staticmethod
    def get_by_source(
        session: Session, source_table: str, source_id: int
    ) -> Optional[CleanDataOut]:
        stmt = (
            select(models.CleanData)
            .where(
                (models.CleanData.source_table == source_table)
                & (models.CleanData.source_id == source_id)
            )
            .limit(1)
        )
        obj = session.execute(stmt).scalars().first()
        return CleanDataOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def mark_error(
        session: Session, clean_id: int, error: Optional[str] = None
    ) -> None:
        values: Dict[str, Any] = {}
        if error is not None:
            values["error"] = error

        if not values:
            return

        stmt = (
            update(models.CleanData)
            .where(models.CleanData.id == clean_id)
            .values(**values)
        )
        session.execute(stmt)
