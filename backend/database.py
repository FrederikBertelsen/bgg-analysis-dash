import sqlite3
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable
from pandas import DataFrame


@dataclass
class BoardGame:
    id: int
    name: str
    url: str
    updated_at: Optional[str] = None

    def to_tuple(self) -> Tuple[int, str, str]:
        return (self.id, self.name, self.url)


class BoardGameDataBase:
    boardgame_table_columns = [
        "id",
        "name",
        "url",
        "updated_at",
    ]
    insert_boardgame_upsert = """
        INSERT INTO boardgames (id, name, url, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            url=excluded.url,
            updated_at=CURRENT_TIMESTAMP;
        """

    # Fallback for older SQLite versions that don't support "ON CONFLICT ... DO UPDATE"
    insert_boardgame_replace = """
        INSERT OR REPLACE INTO boardgames (id, name, url, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP);
        """

    def __init__(self, db_path: str = "backend/sqlite.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        # Choose appropriate insert query depending on SQLite version.
        # `sqlite3.sqlite_version_info` is available in the stdlib.
        if getattr(sqlite3, "sqlite_version_info", (0,)) >= (3, 24, 0):
            self.insert_boardgame_query = self.insert_boardgame_upsert
        else:
            self.insert_boardgame_query = self.insert_boardgame_replace

        # Create table if missing using the connection directly (no persistent cursor).
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boardgames (
                id INT PRIMARY KEY,
                name VARCHAR(255),
                url VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        self._conn.commit()

    def insert_or_update_boardgame(self, boardgame: BoardGame) -> None:
        self._conn.execute(self.insert_boardgame_query, boardgame.to_tuple())
        self._conn.commit()

    def insert_or_update_boardgames(self, boardgames: Iterable[BoardGame]) -> None:
        boardgame_tuples = [bg.to_tuple() for bg in boardgames]
        if not boardgame_tuples:
            return
        self._conn.executemany(self.insert_boardgame_query, boardgame_tuples)
        self._conn.commit()

    def get_boardgames(self) -> DataFrame:
        cur = self._conn.execute("SELECT * FROM boardgames;")
        rows = cur.fetchall()
        if not rows:
            return DataFrame(columns=self.boardgame_table_columns)

        records = [dict(r) for r in rows]
        return DataFrame(records)[self.boardgame_table_columns]

    def close(self) -> None:
        # No persistent cursor is kept; just close the connection.
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
