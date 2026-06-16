import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def fetch_news() -> list[dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/api/news", params={"limit": 200}, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"无法读取日报数据：{exc}")
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


def matches_ecosystem(item: dict, selected: str) -> bool:
    return selected == "全部" or selected in item_ecosystems(item)


def matches_company(item: dict, selected: str) -> bool:
    return selected == "全部" or selected in item_companies(item)


st.set_page_config(page_title="News | Rachel Capital OS Platform", layout="wide")
st.title("News")
st.caption("Daily Intelligence archive and filters")

news_items = fetch_news()

if not news_items:
    st.info("暂无日报数据，请通过 /api/news 接入 Coze 日报。")
    st.stop()

dates = sorted({item["date"] for item in news_items}, reverse=True)
ecosystems = sorted({ecosystem for item in news_items for ecosystem in item_ecosystems(item)})
companies = sorted({company for item in news_items for company in item_companies(item)})

col_date, col_ecosystem, col_company = st.columns(3)
selected_date = col_date.selectbox("日期", ["全部"] + dates)
selected_ecosystem = col_ecosystem.selectbox("生态", ["全部"] + ecosystems)
selected_company = col_company.selectbox("公司", ["全部"] + companies)

filtered_items = news_items
if selected_date != "全部":
    filtered_items = [item for item in filtered_items if item["date"] == selected_date]
filtered_items = [item for item in filtered_items if matches_ecosystem(item, selected_ecosystem)]
filtered_items = [item for item in filtered_items if matches_company(item, selected_company)]

st.subheader(f"日报列表 ({len(filtered_items)})")

for item in filtered_items:
    with st.container(border=True):
        st.markdown(f"**{item['title']}**")
        st.caption(
            f"{item['date']} | {item.get('importance', 'N/A')} | "
            f"{item.get('category') or '未分类'} | {item.get('ecosystem') or '未归属生态'}"
        )
        st.write(item["summary"])
        if item.get("companies"):
            st.write("公司：" + "、".join(item["companies"]))
        if item.get("tags"):
            st.write("标签：" + "、".join(item["tags"]))
        events = item.get("events") or []
        with st.expander(f"事件明细 ({len(events)})"):
            if not events:
                st.write("该日报暂无事件明细。")
            for event in events:
                st.markdown(f"**{event['title']}**")
                st.caption(
                    f"{event.get('importance', 'N/A')} | {event.get('ecosystem') or '未归属生态'}"
                )
                st.write(event["summary"])
                if event.get("impact"):
                    st.write("影响：" + event["impact"])
                if event.get("companies"):
                    st.write("公司：" + "、".join(event["companies"]))
                if event.get("tags"):
                    st.write("标签：" + "、".join(event["tags"]))
