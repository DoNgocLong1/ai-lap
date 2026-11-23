from typing import Literal

from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    content: str = Field(min_length=1, description="Nội dung ticket tiếng Việt")

class TicketOut(BaseModel):
    category: Literal["bug", "feature_request", "question"]
    severity: Literal["low", "medium", "high", "critical"]
    module: str
    summary: str
