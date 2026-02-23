"""Simple DB-backed logger for scrape tasks and lines.

Usage:
    from backend.logger import ScrapeDBLogger

    with ScrapeDBLogger(task_name="browse_boardgames", log_to_console=True) as logger:
        logger.append("Started")
        logger.update_progress(progress=0.1, current_page=1)
        logger.append("Page 1 done")

The logger will create a `ScrapeTask` and write log lines via `ScrapeLogRepository.append_line` using `get_db_session()`.
If an exception is raised within the context, the logger will automatically mark the task as failed and log the exception message.
"""

from typing import Optional, cast

from .database.db import get_db_session
from .repositories import ScrapeTaskRepository, ScrapeLogRepository
from .database.schemas import ScrapeStatus


class ScrapeDBLogger:
    def __init__(
        self,
        task_name: Optional[str] = None,
        task_id: Optional[int] = None,
        log_to_console: bool = False,
    ):
        self.task_name = task_name
        self.task_id = task_id
        self._started = False
        self.log_to_console = log_to_console

    def console_log(self, message: str) -> None:
        if self.log_to_console:
            print(f"[{self.task_id}]: {message}")

    def start(self) -> int:
        if self._started:
            if self.task_id is None:
                raise RuntimeError("Logger already started but task_id is missing")
            return int(cast(int, self.task_id))

        with get_db_session() as session:
            if self.task_id is not None:
                # resume task
                task = ScrapeTaskRepository.get_by_id(
                    session, int(cast(int, self.task_id))
                )
                if task is None:
                    raise ValueError(f"No ScrapeTask with id={self.task_id}")
                self.task_id = int(cast(int, task.id))
                ScrapeTaskRepository.update_progress(
                    session,
                    int(cast(int, self.task_id)),
                    status=ScrapeStatus.running,
                )
            else:
                # new task
                if not self.task_name:
                    raise ValueError(
                        "Either task_name or task_id must be provided to start a task"
                    )
                task = ScrapeTaskRepository.create_task(
                    session, name=self.task_name, status=ScrapeStatus.running
                )
                # convert to int to avoid SQLAlchemy Column typing leaking through
                self.task_id = int(cast(int, task.id))

        self._started = True
        return int(cast(int, self.task_id))

    def log(self, text: str) -> None:
        if self.task_id is None:
            raise ValueError("task_id not set; call start() or provide task_id on init")

        with get_db_session() as session:
            ScrapeLogRepository.append_line(session, int(self.task_id), text)
        self.console_log(text)

    def update_progress(
        self,
        progress: Optional[float] = None,
        status: Optional[ScrapeStatus] = None,
        current_page: Optional[int] = None,
        items_processed: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        if self.task_id is None:
            raise ValueError("task_id not set; call start() or provide task_id on init")

        with get_db_session() as session:
            ScrapeTaskRepository.update_progress(
                session,
                int(self.task_id),
                progress=progress,
                status=status,
                current_page=current_page,
                items_processed=items_processed,
                message=message,
            )

    def finish(self, message: Optional[str] = None) -> None:
        if self.task_id is None:
            return
        with get_db_session() as session:
            ScrapeTaskRepository.update_progress(
                session,
                int(self.task_id),
                progress=1.0,
                status=ScrapeStatus.completed,
                message=message,
            )
            if message:
                ScrapeLogRepository.append_line(session, int(self.task_id), message)
                self.console_log(message)

    def fail(self, message: Optional[str] = None) -> None:
        if self.task_id is None:
            return
        with get_db_session() as session:
            ScrapeTaskRepository.update_progress(
                session,
                int(self.task_id),
                status=ScrapeStatus.failed,
                message=message,
            )
            ScrapeLogRepository.append_line(
                session, int(self.task_id), f"FAILED: {message}"
            )
        self.console_log(f"FAILED: {message}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            # Log failure
            try:
                self.fail(str(exc))
            except Exception:
                pass
        else:
            try:
                self.finish()
            except Exception:
                pass
