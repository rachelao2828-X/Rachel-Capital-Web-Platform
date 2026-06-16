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


st.set_page_config(page_title="News | Rachel Capital OS Platform", layout="wide")
st.title("News")
st.caption("Daily Intelligence archive and filters")

news_items = fetch_news()

if not news_items:
    st.info("暂无日报数据，请通过 /api/news 接入 Coze 日报。")
    st.stop()

dates = sorted({item["date"] for item in news_items}, reverse=True)
ecosystems = sorted({item.get("ecosystem") for item in news_items if item.get("ecosystem")})
companies = sorted({company for item in news_items for company in item.get("companies", [])})

col_date, col_ecosystem, col_company = st.columns(3)
selected_date = col_date.selectbox("日期", ["全部"] + dates)
selected_ecosystem = col_ecosystem.selectbox("生态", ["全部"] + ecosystems)
selected_company = col_company.selectbox("公司", ["全部"] + companies)

filtered_items = news_items
if selected_date != "全部":
    filtered_items = [item for item in filtered_items if item["date"] == selected_date]
if selected_ecosystem != "全部":
    filtered_items = [item for item in filtered_items if item.get("ecosystem") == selected_ecosystem]
if selected_company != "全部":
    filtered_items = [item for item in filtered_items if selected_company in item.get("companies", [])]

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

