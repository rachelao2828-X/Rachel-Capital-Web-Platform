from fastapi.testclient import TestClient

from app.api.main import app


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
    assert body["title"] == "今日科技投资日报"
    assert body["source"] == "coze"
    assert body["companies"] == ["OpenAI", "NVIDIA", "中际旭创"]


def test_get_news() -> None:
    title = "今日科技投资日报 - GET Smoke"
    with TestClient(app) as client:
        client.post("/api/news", json=sample_payload(title=title))
        response = client.get("/api/news")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(item["title"] == title for item in body)
