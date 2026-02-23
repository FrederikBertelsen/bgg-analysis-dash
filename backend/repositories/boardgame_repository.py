from typing import Iterable, List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
import pandas as pd

from .base_repository import BaseRepository
from .. import models
from ..schemas import BoardGameIn


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
