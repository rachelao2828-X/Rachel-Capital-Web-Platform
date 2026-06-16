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
    latest_update = max(item.get("updated_at", "") for item in news_items)
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Daily Intelligence", len(news_items))
    col_b.metric("生态数量", len({item.get("ecosystem") for item in news_items if item.get("ecosystem")}))
    col_c.metric(
        "重点公司",
        len({company for item in news_items for company in item.get("companies", [])}),
    )
    col_d.metric("最近更新时间", latest_update[:19].replace("T", " ") if latest_update else "N/A")

    st.subheader("今日十大科技投资事件")
    for item in news_items[:10]:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            st.caption(
                f"{item['date']} | {item.get('importance', 'N/A')} | "
                f"{item.get('category') or '未分类'} | {item.get('ecosystem') or '未归属生态'}"
            )
            st.write(item["summary"])
            companies = item.get("companies") or []
            tags = item.get("tags") or []
            if companies:
                st.write("重点公司：" + "、".join(companies))
            if tags:
                st.write("标签：" + "、".join(tags))

    st.subheader("按生态分类")
    ecosystems: dict[str, list[dict]] = {}
    for item in news_items:
        ecosystems.setdefault(item.get("ecosystem") or "未归属生态", []).append(item)
    for ecosystem, items in ecosystems.items():
        with st.expander(f"{ecosystem} ({len(items)})"):
            for item in items:
                st.write(f"- {item['date']} | {item['title']}")

    st.subheader("重点公司")
    company_counts: dict[str, int] = {}
    for item in news_items:
        for company in item.get("companies", []):
            company_counts[company] = company_counts.get(company, 0) + 1
    if company_counts:
        st.write(
            [
                {"company": company, "news_count": count}
                for company, count in sorted(company_counts.items(), key=lambda row: row[1], reverse=True)
            ]
        )
