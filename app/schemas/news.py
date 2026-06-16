from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsEventBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    ecosystem: str | None = None
    companies: list[str] = Field(default_factory=list)
    impact: str | None = None
    importance: str = Field(default="medium", max_length=32)
    tags: list[str] = Field(default_factory=list)


class NewsEventCreate(NewsEventBase):
    pass


class NewsEventRead(NewsEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    news_item_id: int
    created_at: datetime
    updated_at: datetime


class NewsItemBase(BaseModel):
    date: date
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    importance: str = Field(default="medium", max_length=32)
    category: str | None = None
    ecosystem: str | None = None
    companies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str = Field(default="coze", max_length=80)


class NewsItemCreate(NewsItemBase):
    events: list[NewsEventCreate] = Field(default_factory=list)


class NewsItemRead(NewsItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    obsidian_sync: str = "skipped"
    git_sync: str = "skipped"
    obsidian_path: str | None = None
    last_synced_at: datetime | None = None
    events: list[NewsEventRead] = Field(default_factory=list)


class NewsItemCreateResponse(BaseModel):
    status: str
    news_id: int
    db_sync: str
    obsidian_sync: str
    git_sync: str
