from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
import pytest

from app.api.main import app
from app.core.config import settings
from app.services.git_service import sync_obsidian_vault_to_git


@pytest.fixture(autouse=True)
def local_dev_settings(monkeypatch):
    monkeypatch.setattr(settings, "coze_webhook_secret", None)


def sample_payload(title: str = "今日科技投资日报") -> dict:
    return {
        "date": "2026-06-16",
        "title": title,
        "summary": "摘要",
        "importance": "high",
        "category": "AI",
        "ecosystem": "AI基础设施生态",
        "companies": ["OpenAI", "NVIDIA", "中际旭创"],
        "tags": ["AI", "算力", "光模块"],
        "source": "coze",
        "events": [
            {
                "title": "AI 算力基础设施继续扩张",
                "summary": "头部 AI 公司继续推动推理与训练基础设施投入。",
                "ecosystem": "AI基础设施生态",
                "companies": ["OpenAI", "NVIDIA"],
                "impact": "提升算力链条景气度。",
                "importance": "high",
                "tags": ["AI", "算力"],
            }
        ],
    }


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_news() -> None:
    with TestClient(app) as client:
        response = client.post("/api/news", json=sample_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ok"
    assert body["db_sync"] == "success"
    assert body["obsidian_sync"] in {"skipped_not_configured", "success", "failed"}


def test_get_news() -> None:
    title = "今日科技投资日报 - GET Smoke"
    with TestClient(app) as client:
        client.post("/api/news", json=sample_payload(title=title))
        response = client.get("/api/news")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(item["title"] == title for item in body)
    assert any(item["events"] for item in body if item["title"] == title)


def test_obsidian_path_unconfigured_api_does_not_crash(monkeypatch) -> None:
    monkeypatch.setattr(settings, "obsidian_vault_path", "")
    monkeypatch.setattr(settings, "git_auto_commit", True)

    with TestClient(app) as client:
        response = client.post("/api/news", json=sample_payload(title="未配置 Obsidian 测试"))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ok"
    assert body["obsidian_sync"] == "skipped_not_configured"
    assert body["git_sync"] == "skipped"


def test_obsidian_path_configured_generates_markdown(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "daily_report_obsidian_dir", "31_Inbox/Daily_Intelligence")
    monkeypatch.setattr(settings, "git_auto_commit", False)

    with TestClient(app) as client:
        response = client.post("/api/news", json=sample_payload(title="生成 Markdown 测试"))

    assert response.status_code == 201
    body = response.json()
    assert body["obsidian_sync"] == "success"
    assert body["git_sync"] == "skipped_disabled"

    markdown_file = tmp_path / "31_Inbox" / "Daily_Intelligence" / "2026-06-16_科技投资日报.md"
    assert markdown_file.exists()
    content = markdown_file.read_text(encoding="utf-8")
    assert "2026-06-16 科技投资日报" in content
    assert "AI 算力基础设施继续扩张" in content
    assert "source: platform" in content


def test_news_test_endpoint_generates_daily_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "daily_report_obsidian_dir", "31_Inbox/Daily_Intelligence")
    monkeypatch.setattr(settings, "git_auto_commit", False)

    with TestClient(app) as client:
        response = client.get("/api/news/test")

    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "obsidian_sync": "success"}

    files = list((tmp_path / "31_Inbox" / "Daily_Intelligence").glob("*_科技投资日报.md"))
    assert files
    content = files[0].read_text(encoding="utf-8")
    assert "OpenAI 发布新一代 Agent SDK" in content
    assert "可能进一步提升推理算力需求和 Agent 应用渗透率。" in content


def test_git_non_repo_skips(tmp_path: Path) -> None:
    result = sync_obsidian_vault_to_git(
        report_date="2026-06-16",
        vault_path=str(tmp_path),
        auto_commit=True,
        branch="develop",
    )

    assert result.status == "skipped_not_git_repo"


def test_git_no_changes_skips_commit(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)

    result = sync_obsidian_vault_to_git(
        report_date="2026-06-16",
        vault_path=str(tmp_path),
        auto_commit=True,
        branch="develop",
    )

    assert result.status == "skipped_no_changes"
