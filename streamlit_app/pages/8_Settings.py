import os
from pathlib import Path
import subprocess

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


def exists_status(path_value: str | None) -> str:
    if not path_value:
        return "未配置"
    return "存在" if Path(path_value).expanduser().exists() else "不存在"


def daily_dir_status(vault_path: str | None, daily_dir: str | None) -> str:
    if not vault_path:
        return "未配置"
    target = Path(vault_path).expanduser() / (daily_dir or "31_Inbox/Daily_Intelligence")
    return "存在" if target.exists() else "不存在"


def git_repo_status(vault_path: str | None) -> str:
    if not vault_path:
        return "未配置"
    vault = Path(vault_path).expanduser()
    if not vault.exists():
        return "路径不存在"
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=vault,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return "是" if result.returncode == 0 and result.stdout.strip() == "true" else "否"


st.set_page_config(page_title="Settings | Rachel Capital OS Platform", layout="wide")
st.title("Settings")
st.caption("Configuration status only. Secret values are not displayed.")

vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
daily_dir = os.getenv("DAILY_REPORT_OBSIDIAN_DIR", "31_Inbox/Daily_Intelligence")

rows = [
    {"item": "DATABASE_URL", "status": database_status(os.getenv("DATABASE_URL"))},
    {"item": "OBSIDIAN_VAULT_PATH 是否配置", "status": configured(vault_path)},
    {"item": "OBSIDIAN_VAULT_PATH 是否存在", "status": exists_status(vault_path)},
    {"item": "Daily Intelligence 目录是否存在", "status": daily_dir_status(vault_path, daily_dir)},
    {"item": "是否为 Git 仓库", "status": git_repo_status(vault_path)},
    {"item": "GIT_AUTO_COMMIT 是否开启", "status": os.getenv("GIT_AUTO_COMMIT", "true")},
    {"item": "COZE_WEBHOOK_SECRET", "status": configured(os.getenv("COZE_WEBHOOK_SECRET"))},
    {"item": "FEISHU_WEBHOOK_URL", "status": configured(os.getenv("FEISHU_WEBHOOK_URL"))},
    {"item": "GITHUB_TOKEN", "status": configured(os.getenv("GITHUB_TOKEN"))},
]

st.table(rows)
