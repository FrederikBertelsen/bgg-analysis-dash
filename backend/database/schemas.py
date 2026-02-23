from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


class BoardGameIn(BaseModel):
    id: int
    name: str
    url: str


class ScrapeStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ScrapeTaskCreate(BaseModel):
    name: str
    status: Optional[ScrapeStatus] = ScrapeStatus.pending
    progress: Optional[float] = 0.0


class ScrapeTaskUpdate(BaseModel):
    status: Optional[ScrapeStatus]
    progress: Optional[float]
    current_page: Optional[int]
    items_processed: Optional[int]
    message: Optional[str]


class ScrapeLogLine(BaseModel):
    task_id: int
    line_no: Optional[int] = None
    text: str
