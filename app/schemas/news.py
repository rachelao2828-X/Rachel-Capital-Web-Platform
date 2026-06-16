from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsItemCreate(BaseModel):
    date: date
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    importance: str = Field(default="medium", max_length=32)
    category: str | None = None
    ecosystem: str | None = None
    companies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str = Field(default="coze", max_length=80)


class NewsItemRead(NewsItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

