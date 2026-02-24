from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from backend.utils import estimate_eta
from pydantic import model_validator


class BoardGameIn(BaseModel):
    id: int
    name: str
    url: str


class ScrapeStatus(str, Enum):
    none = "none"
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ScrapeTaskCreate(BaseModel):
    name: str
    status: Optional[ScrapeStatus] = ScrapeStatus.none
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


class BoardGameOut(BaseModel):
    id: int
    name: str
    url: str

    model_config = {"from_attributes": True}


class RawDataIn(BaseModel):
    source_table: str
    source_id: Optional[int] = None
    scrape_task_id: Optional[int] = None
    payload: Dict[str, Any]
    processor_version: Optional[str] = None


class RawDataOut(BaseModel):
    id: int
    source_table: str
    source_id: Optional[int]
    scrape_task_id: Optional[int]
    payload: Dict[str, Any]
    processed: bool
    processor_version: Optional[str]
    error: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ScrapeTaskOut(BaseModel):
    id: int
    name: str
    status: ScrapeStatus
    progress: float
    current_page: Optional[int]
    items_processed: Optional[int]
    message: Optional[str]
    created_at: Optional[datetime]
    last_update: Optional[datetime]
    eta: Optional[str] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_eta(self):
        try:
            is_running = self.status == ScrapeStatus.running
            if is_running:
                self.eta = estimate_eta(
                    self.progress, self.last_update, self.created_at
                )
            else:
                self.eta = None
        except Exception:
            self.eta = None
        return self


class ScrapeLogLineOut(BaseModel):
    id: int
    task_id: int
    line_no: int
    text: str
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
