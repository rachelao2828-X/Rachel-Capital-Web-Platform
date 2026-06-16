import os

import streamlit as st


def configured(value: str | None) -> str:
    return "已配置" if value else "未配置"


def database_status(value: str | None) -> str:
    if not value:
        return "未配置"
    if value.startswith("sqlite"):
        return "已配置 (SQLite)"
    if value.startswith("postgresql"):
        return "已配置 (PostgreSQL)"
    return "已配置"


st.set_page_config(page_title="Settings | Rachel Capital OS Platform", layout="wide")
st.title("Settings")
st.caption("Configuration status only. Secret values are not displayed.")

rows = [
    {"item": "DATABASE_URL", "status": database_status(os.getenv("DATABASE_URL"))},
    {"item": "OBSIDIAN_VAULT_PATH", "status": configured(os.getenv("OBSIDIAN_VAULT_PATH"))},
    {"item": "COZE_WEBHOOK_SECRET", "status": configured(os.getenv("COZE_WEBHOOK_SECRET"))},
    {"item": "FEISHU_WEBHOOK_URL", "status": configured(os.getenv("FEISHU_WEBHOOK_URL"))},
    {"item": "GITHUB_TOKEN", "status": configured(os.getenv("GITHUB_TOKEN"))},
]

st.table(rows)
