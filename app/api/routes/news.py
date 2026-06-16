from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.news import NewsEvent, NewsItem
from app.schemas.news import NewsItemCreate, NewsItemRead

router = APIRouter(prefix="/api/news", tags=["Daily Intelligence"])


def verify_coze_secret(x_coze_secret: str | None = Header(default=None)) -> None:
    if settings.coze_webhook_secret and x_coze_secret != settings.coze_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Coze-Secret header.",
        )


@router.post("", response_model=NewsItemRead, status_code=status.HTTP_201_CREATED)
def create_news_item(
    payload: NewsItemCreate,
    _: None = Depends(verify_coze_secret),
    db: Session = Depends(get_db),
) -> NewsItem:
    news_item = NewsItem(**payload.model_dump(exclude={"events"}))
    news_item.events = [NewsEvent(**event.model_dump()) for event in payload.events]
    db.add(news_item)
    db.commit()
    db.refresh(news_item)
    news_item.events
    return news_item


@router.get("", response_model=list[NewsItemRead])
def list_news_items(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    news_date: date | None = Query(default=None, alias="date"),
    ecosystem: str | None = None,
    company: str | None = None,
) -> list[NewsItem]:
    statement = (
        select(NewsItem)
        .options(selectinload(NewsItem.events))
        .order_by(NewsItem.date.desc(), NewsItem.created_at.desc())
        .limit(limit)
    )
    if news_date is not None:
        statement = statement.where(NewsItem.date == news_date)

    items = list(db.scalars(statement).all())
    if ecosystem:
        ecosystem_lower = ecosystem.lower()
        items = [
            item
            for item in items
            if (item.ecosystem and ecosystem_lower in item.ecosystem.lower())
            or any(
                event.ecosystem and ecosystem_lower in event.ecosystem.lower()
                for event in (item.events or [])
            )
        ]
    if company:
        company_lower = company.lower()
        items = [
            item
            for item in items
            if any(company_lower in company_name.lower() for company_name in (item.companies or []))
            or any(
                company_lower in company_name.lower()
                for event in (item.events or [])
                for company_name in (event.companies or [])
            )
        ]
    return items
