from typing import Any, List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from .base_repository import BaseRepository
from ..database import models, schemas
from ..database.schemas import RawDataIn, RawDataOut


class RawDataRepository(BaseRepository):
    @staticmethod
    def create(session: Session, raw_in: RawDataIn) -> RawDataOut:
        raw = models.RawData(
            source_table=raw_in.source_table,
            source_id=raw_in.source_id,
            scrape_task_id=raw_in.scrape_task_id,
            payload=raw_in.payload,
            processor_version=raw_in.processor_version,
        )
        session.add(raw)
        session.flush()
        session.refresh(raw)
        return RawDataOut.model_validate(raw)

    @staticmethod
    def get_by_id(session: Session, raw_id: int) -> Optional[RawDataOut]:
        raw = session.get(models.RawData, raw_id)
        return RawDataOut.model_validate(raw) if raw is not None else None

    @staticmethod
    def get_by_scrape_task_id(
        session: Session, scrape_task_id: int
    ) -> List[RawDataOut]:
        stmt = select(models.RawData).where(
            models.RawData.scrape_task_id == scrape_task_id
        )
        objs = list(session.execute(stmt).scalars().all())
        return [RawDataOut.model_validate(o) for o in objs]

    @staticmethod
    def get_by_source(
        session: Session, source_table: str, source_id: int
    ) -> Optional[RawDataOut]:
        stmt = (
            select(models.RawData)
            .where(
                (models.RawData.source_table == source_table)
                & (models.RawData.source_id == source_id)
            )
            .limit(1)
        )
        obj = session.execute(stmt).scalars().first()
        return RawDataOut.model_validate(obj) if obj is not None else None

    @staticmethod
    def get_by_source_table(session: Session, source_table: str) -> List[RawDataOut]:
        stmt = select(models.RawData).where(models.RawData.source_table == source_table)
        objs = list(session.execute(stmt).scalars().all())
        return [RawDataOut.model_validate(o) for o in objs]

    @staticmethod
    def mark_processed(
        session: Session,
        raw_id: int,
        processed: bool = True,
        processor_version: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        values: Dict[str, Any] = {"processed": processed}
        if processor_version is not None:
            values["processor_version"] = processor_version
        if error is not None:
            values["error"] = error

        stmt = (
            update(models.RawData).where(models.RawData.id == raw_id).values(**values)
        )
        session.execute(stmt)
