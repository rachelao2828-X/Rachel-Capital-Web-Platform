from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.news import NewsEvent, NewsItem
from app.schemas.news import NewsItemCreate, NewsItemCreateResponse, NewsItemRead
from app.services.git_service import sync_obsidian_vault_to_git
from app.services.obsidian_service import write_daily_report_to_obsidian

router = APIRouter(prefix="/api/news", tags=["Daily Intelligence"])


def verify_coze_secret(x_coze_secret: str | None = Header(default=None)) -> None:
    if settings.coze_webhook_secret and x_coze_secret != settings.coze_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Coze-Secret header.",
        )


def save_news_item_with_pipeline(payload: NewsItemCreate, db: Session) -> NewsItemCreateResponse:
    news_item = NewsItem(**payload.model_dump(exclude={"events"}))
    news_item.events = [NewsEvent(**event.model_dump()) for event in payload.events]
    db.add(news_item)
    db.commit()
    db.refresh(news_item)
    news_item.events

    try:
        obsidian_result = write_daily_report_to_obsidian(news_item)
    except Exception as exc:
        obsidian_result_status = "failed"
        obsidian_path = None
        obsidian_detail = str(exc)
    else:
        obsidian_result_status = obsidian_result.status
        obsidian_path = obsidian_result.path
        obsidian_detail = obsidian_result.detail

    if obsidian_result_status == "success":
        try:
            git_result = sync_obsidian_vault_to_git(report_date=news_item.date.isoformat())
            git_sync = git_result.status
        except Exception as exc:
            git_sync = "failed"
            obsidian_detail = obsidian_detail or str(exc)
    else:
        git_sync = "skipped"

    news_item.obsidian_sync = obsidian_result_status
    news_item.git_sync = git_sync
    news_item.obsidian_path = obsidian_path or obsidian_detail
    news_item.last_synced_at = datetime.now(timezone.utc)
    db.add(news_item)
    db.commit()

    return NewsItemCreateResponse(
        status="ok",
        news_id=news_item.id,
        db_sync="success",
        obsidian_sync=obsidian_result_status,
        obsidian_path=obsidian_path,
        git_sync=git_sync,
    )


@router.post("", response_model=NewsItemCreateResponse, status_code=status.HTTP_201_CREATED)
def create_news_item(
    payload: NewsItemCreate,
    _: None = Depends(verify_coze_secret),
    db: Session = Depends(get_db),
) -> NewsItemCreateResponse:
    return save_news_item_with_pipeline(payload=payload, db=db)


@router.get("/test")
def create_test_news_item(db: Session = Depends(get_db)) -> dict[str, str]:
    payload = NewsItemCreate(
        date=date.today(),
        title="OpenAI 发布新一代 Agent SDK",
        summary="OpenAI 发布新一代 Agent SDK，进一步降低智能体应用开发门槛。",
        importance="high",
        category="AI",
        ecosystem="AI基础设施生态",
        companies=["OpenAI", "NVIDIA", "微软"],
        tags=["科技投资", "AI", "Agent"],
        source="platform",
        events=[
            {
                "title": "OpenAI 发布新一代 Agent SDK",
                "summary": "OpenAI 发布新一代 Agent SDK，可能加速 Agent 应用开发和企业级落地。",
                "ecosystem": "AI基础设施生态",
                "companies": ["OpenAI", "NVIDIA", "微软"],
                "impact": "可能进一步提升推理算力需求和 Agent 应用渗透率。",
                "importance": "high",
                "tags": ["AI", "Agent", "推理算力"],
            }
        ],
    )
    result = save_news_item_with_pipeline(payload=payload, db=db)
    return {
        "status": result.status,
        "obsidian_sync": result.obsidian_sync,
        "obsidian_path": result.obsidian_path or "",
    }


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
