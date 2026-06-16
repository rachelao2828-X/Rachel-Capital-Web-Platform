import os

import requests
import streamlit as st


APP_NAME = os.getenv("APP_NAME", "Rachel Capital OS Platform")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def fetch_news() -> list[dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/api/news", params={"limit": 50}, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def item_companies(item: dict) -> set[str]:
    companies = set(item.get("companies") or [])
    for event in item.get("events") or []:
        companies.update(event.get("companies") or [])
    return companies


def item_ecosystems(item: dict) -> set[str]:
    ecosystems = set()
    if item.get("ecosystem"):
        ecosystems.add(item["ecosystem"])
    for event in item.get("events") or []:
        if event.get("ecosystem"):
            ecosystems.add(event["ecosystem"])
    return ecosystems


def item_events(item: dict) -> list[dict]:
    events = item.get("events") or []
    if events:
        return events
    return [
        {
            "title": item["title"],
            "summary": item["summary"],
            "ecosystem": item.get("ecosystem"),
            "companies": item.get("companies") or [],
            "impact": None,
            "importance": item.get("importance"),
            "tags": item.get("tags") or [],
        }
    ]


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
)

st.title("Rachel Capital OS Platform")
st.caption("Daily Intelligence MVP")

news_items = fetch_news()

if not news_items:
    st.info("暂无日报数据，请通过 /api/news 接入 Coze 日报。")
else:
    latest_date = max(item["date"] for item in news_items)
    today_items = [item for item in news_items if item["date"] == latest_date]
    today_events = [event for item in today_items for event in item_events(item)]
    associated_companies = sorted({company for item in today_items for company in item_companies(item)})
    associated_ecosystems = sorted({ecosystem for item in today_items for ecosystem in item_ecosystems(item)})
    latest_update = max(item.get("updated_at", "") for item in news_items)
    latest_sync = max((item.get("last_synced_at") or "" for item in news_items), default="")
    latest_item = max(news_items, key=lambda item: item.get("updated_at", ""))

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("今日日报", len(today_items))
    col_b.metric("今日事件", len(today_events))
    col_c.metric("关联公司", len(associated_companies))
    col_d.metric("最近更新时间", latest_update[:19].replace("T", " ") if latest_update else "N/A")

    sync_a, sync_b, sync_c = st.columns(3)
    sync_a.metric("Obsidian 同步状态", latest_item.get("obsidian_sync", "skipped"))
    sync_b.metric("GitHub 备份状态", latest_item.get("git_sync", "skipped"))
    sync_c.metric("最近同步时间", latest_sync[:19].replace("T", " ") if latest_sync else "N/A")

    st.subheader("今日日报摘要")
    for item in today_items:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            st.caption(
                f"{item['date']} | {item.get('importance', 'N/A')} | "
                f"{item.get('category') or '未分类'} | {item.get('source') or 'unknown'}"
            )
            st.write(item["summary"])

    st.subheader("今日十大科技投资事件")
    for event in today_events[:10]:
        with st.container(border=True):
            st.markdown(f"**{event['title']}**")
            st.caption(
                f"{event.get('importance', 'N/A')} | {event.get('ecosystem') or '未归属生态'}"
            )
            st.write(event["summary"])
            if event.get("impact"):
                st.write("影响：" + event["impact"])
            companies = event.get("companies") or []
            tags = event.get("tags") or []
            if companies:
                st.write("关联公司：" + "、".join(companies))
            if tags:
                st.write("标签：" + "、".join(tags))

    st.subheader("关联公司")
    if associated_companies:
        st.write("、".join(associated_companies))
    else:
        st.write("暂无关联公司")

    st.subheader("关联战略生态")
    if associated_ecosystems:
        st.write("、".join(associated_ecosystems))
    else:
        st.write("暂无关联战略生态")
