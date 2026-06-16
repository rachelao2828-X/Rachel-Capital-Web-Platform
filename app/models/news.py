from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    importance = Column(String(32), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=True)
    ecosystem = Column(String(150), index=True, nullable=True)
    companies = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    source = Column(String(80), index=True, nullable=False, default="coze")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    events = relationship(
        "NewsEvent",
        back_populates="news_item",
        cascade="all, delete-orphan",
        order_by="NewsEvent.id",
    )


class NewsEvent(Base):
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, index=True)
    news_item_id = Column(Integer, ForeignKey("news_items.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    ecosystem = Column(String(150), index=True, nullable=True)
    companies = Column(JSON, default=list, nullable=False)
    impact = Column(Text, nullable=True)
    importance = Column(String(32), index=True, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    news_item = relationship("NewsItem", back_populates="events")
