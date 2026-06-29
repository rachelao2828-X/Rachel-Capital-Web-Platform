import pandas as pd
import streamlit as st

from app.services.company_pool_loader import load_company_pool_overview, load_ecosystem_company_pools
from app.services.ecosystem_loader import (
    SECTION_ALIASES,
    load_ecosystem,
    load_ecosystem_cross_map,
    load_ecosystems,
)
from app.services.quarterly_tracking_loader import (
    load_ecosystem_quarterly_trackings,
    load_quarterly_tracking_overview,
)
from research_engine.company_database_loader import (
    build_company_database_linkage,
    ecosystem_statistics_rows,
    market_statistics_rows,
)


def company_link_table_row(row: dict) -> dict:
    return {
        "公司 / 项目": row.get("company_name", ""),
        "市场类型": row.get("market_type", ""),
        "代码": row.get("ticker", ""),
        "细分环节": row.get("segment", ""),
        "生态相关性": row.get("ecosystem_relevance", ""),
        "研究优先级": row.get("research_priority", ""),
        "当前研究状态": row.get("research_status", ""),
        "匹配方式": row.get("match_type", ""),
        "关联文件": row.get("linked_file") or "待建档",
        "来源状态": row.get("source_status", ""),
    }


def ecosystem_detail_link_row(row: dict) -> dict:
    return {
        "公司 / 项目": row.get("company_name", ""),
        "市场类型": row.get("market_type", ""),
        "代码": row.get("ticker", ""),
        "细分环节": row.get("segment", ""),
        "生态相关性": row.get("ecosystem_relevance", ""),
        "研究优先级": row.get("research_priority", ""),
        "当前研究状态": row.get("research_status", ""),
        "匹配方式": row.get("match_type", ""),
        "关联文件": row.get("linked_file") or "待建档",
    }


def company_option_label(row: dict) -> str:
    ticker = row.get("ticker") or "无代码"
    source_status = row.get("source_status") or "待完善"
    return f"{row.get('company_name') or '未命名'}｜{row.get('market_type') or '其他'}｜{ticker}｜{source_status}"


st.set_page_config(page_title="战略生态 | Rachel Capital OS", layout="wide")

st.title("战略生态")
st.caption("本地 Obsidian 研究文件读取视图，仅用于 localhost 内部研究管理。")

overview_tab, cross_map_tab, company_pool_tab, quarterly_tracking_tab = st.tabs(
    ["七大战略生态", "生态交叉关系", "生态公司池", "生态季度跟踪"]
)

company_pools_for_linkage = load_ecosystem_company_pools()
company_database_linkage = build_company_database_linkage(None, company_pools_for_linkage)

with cross_map_tab:
    cross_map = load_ecosystem_cross_map()
    st.header(cross_map["name"])
    st.write(f"状态：**{cross_map['status']}**")
    st.write(f"Obsidian 文件路径：`{cross_map['file_path']}`")

    if cross_map["status"] != "已读取":
        st.info("待建设")
    else:
        if cross_map.get("public") is not False:
            st.warning("该内部研究文件应设置 frontmatter：public: false")

        st.subheader("七大生态关系说明")
        summary = str(cross_map.get("summary") or "")
        st.markdown(summary if summary else "暂无内容。")

        st.subheader("生态交叉矩阵")
        matrix = cross_map.get("cross_matrix") or []
        if matrix:
            st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
        else:
            st.info("暂未解析到生态交叉矩阵。")

        st.subheader("高优先级交叉主题")
        priority_themes = cross_map.get("priority_themes") or []
        if priority_themes:
            for theme in priority_themes:
                with st.expander(str(theme.get("title") or "主题"), expanded=False):
                    st.markdown(str(theme.get("content") or ""))
        else:
            st.info("暂未解析到高优先级交叉主题。")

        st.subheader("交叉关系跟踪指标")
        tracking_indicators = cross_map.get("tracking_indicators") or []
        if tracking_indicators:
            for indicator in tracking_indicators:
                with st.expander(str(indicator.get("title") or "指标"), expanded=False):
                    st.markdown(str(indicator.get("content") or ""))
        else:
            st.info("暂未解析到跟踪指标。")

        st.subheader("原文预览")
        st.text_area("交叉关系图谱原文预览", str(cross_map.get("raw_markdown") or ""), height=360)

with company_pool_tab:
    overview = load_company_pool_overview()
    company_pools = company_pools_for_linkage

    st.header("战略生态公司池")
    st.write(f"总览状态：**{overview['status']}**")
    st.write(f"总览文件路径：`{overview['file_path']}`")
    st.info("后续将支持从公司池选择公司或一级市场项目，并跳转到 Valuation Cockpit 进行估值与尽调。")
    st.write("查看生态交叉关系图谱：`七大战略生态交叉关系图谱`")

    if overview["status"] != "已读取":
        st.warning("公司池总览待建设。")
    elif overview.get("public") is not False:
        st.warning("公司池总览文件应设置 frontmatter：public: false")

    st.subheader("公司数据库联动")
    st.write(f"公司数据库状态：**{company_database_linkage['status']}**")
    st.write(f"读取路径：`{company_database_linkage['root_path']}`")
    metric_cols = st.columns(4)
    metric_cols[0].metric("已读取公司 / 项目", int(company_database_linkage.get("company_count") or 0))
    metric_cols[1].metric("未匹配公司", len(company_database_linkage.get("unmatched_companies") or []))
    metric_cols[2].metric("待人工确认", len(company_database_linkage.get("pending_confirmation") or []))
    metric_cols[3].metric("公司池数量", len(company_pools))

    linkage_tabs = st.tabs(["按市场类型统计", "按战略生态统计", "读取提示"])
    with linkage_tabs[0]:
        st.dataframe(pd.DataFrame(market_statistics_rows(company_database_linkage)), use_container_width=True, hide_index=True)
    with linkage_tabs[1]:
        st.dataframe(
            pd.DataFrame(ecosystem_statistics_rows(company_database_linkage)),
            use_container_width=True,
            hide_index=True,
        )
    with linkage_tabs[2]:
        warnings = company_database_linkage.get("warnings") or []
        st.markdown("\n".join(f"- {item}" for item in warnings) if warnings else "暂无读取提示。")

    pool_cols = st.columns(2)
    for index, pool in enumerate(company_pools):
        with pool_cols[index % 2]:
            with st.container(border=True):
                st.subheader(str(pool["name"]))
                st.caption(str(pool["status"]))
                st.write(f"所属战略生态：`{pool['ecosystem']}`")
                st.write(f"Obsidian 文件：`{pool['file_path']}`")
                public_label = "未标明" if pool.get("public") is None else str(pool.get("public")).lower()
                st.write(f"`public`: `{public_label}`")

                if pool["status"] != "已读取":
                    st.warning("待建设")
                    continue
                if pool.get("public") is not False:
                    st.warning("该内部研究文件应设置 frontmatter：public: false")

                companies = pool.get("companies") or []
                st.write(f"公司池表格预览：{len(companies)} 条")
                if companies:
                    st.dataframe(pd.DataFrame(companies), use_container_width=True, hide_index=True)
                else:
                    st.info("暂未解析到公司池表格。")

                linked_rows = (
                    (company_database_linkage.get("matches") or {})
                    .get(str(pool.get("ecosystem") or ""), {})
                    .get("matched_companies", [])
                )
                if linked_rows:
                    st.write(f"关联公司 / 项目：{len(linked_rows)} 条")
                    st.dataframe(
                        pd.DataFrame([company_link_table_row(row) for row in linked_rows]),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("暂未匹配到关联公司 / 项目。")

                detail_tabs = st.tabs(["细分环节", "高优先级跟踪对象", "待补充清单", "原文预览"])
                with detail_tabs[0]:
                    segments = pool.get("segments") or []
                    st.markdown("\n".join(f"- {item}" for item in segments) if segments else "暂无内容。")
                with detail_tabs[1]:
                    priority_targets = pool.get("priority_targets") or []
                    st.markdown(
                        "\n".join(f"- {item}" for item in priority_targets) if priority_targets else "暂无内容。"
                    )
                with detail_tabs[2]:
                    to_fill = pool.get("to_fill") or []
                    st.markdown("\n".join(f"- {item}" for item in to_fill) if to_fill else "暂无内容。")
                with detail_tabs[3]:
                    st.text_area(
                        "公司池原文预览",
                        str(pool.get("raw_markdown") or ""),
                        height=260,
                        key=f"company_pool_preview_{pool['ecosystem']}",
                    )

    all_linked_rows = [
        row
        for match in (company_database_linkage.get("matches") or {}).values()
        for row in match.get("matched_companies", [])
    ]
    st.subheader("公司卡片摘要预览")
    if all_linked_rows:
        selected_label = st.selectbox(
            "选择公司 / 项目",
            [company_option_label(row) for row in all_linked_rows],
            key="company_pool_linked_company_selector",
        )
        selected_index = [company_option_label(row) for row in all_linked_rows].index(selected_label)
        selected_company = all_linked_rows[selected_index]
        preview_cols = st.columns(3)
        preview_cols[0].write(f"公司名称：`{selected_company.get('company_name') or ''}`")
        preview_cols[1].write(f"市场类型：`{selected_company.get('market_type') or ''}`")
        preview_cols[2].write(f"代码：`{selected_company.get('ticker') or ''}`")
        st.write(f"核心业务：{selected_company.get('core_business') or selected_company.get('summary') or '待补充'}")
        st.write(f"研究状态：`{selected_company.get('research_status') or '待补充'}`")
        st.write(f"研究优先级：`{selected_company.get('research_priority') or '待补充'}`")
        st.write(f"关联文件：`{selected_company.get('linked_file') or '待建档'}`")
        st.write(f"来源状态：`{selected_company.get('source_status') or '待完善'}`")
        st.markdown("#### 估值驾驶舱联动")
        st.info("后续将支持从公司数据库或战略生态公司池选择公司 / 项目，并进入 Valuation Cockpit 进行估值与尽调。")
        if st.button("发送到估值驾驶舱（预留）", key="send_company_to_valuation"):
            st.session_state["selected_company_for_valuation"] = selected_company
            st.success("已写入 session_state，等待后续 Valuation Cockpit 联动。")
        st.text_area(
            "原始 Markdown 预览",
            str(selected_company.get("raw_markdown") or selected_company.get("summary") or "暂无公司卡片原文。"),
            height=260,
        )
    else:
        st.info("暂无可预览公司 / 项目。")

with quarterly_tracking_tab:
    tracking_overview = load_quarterly_tracking_overview()
    trackings = load_ecosystem_quarterly_trackings()

    st.header("生态季度跟踪")
    st.write(f"总览状态：**{tracking_overview['status']}**")
    st.write(f"总览文件路径：`{tracking_overview['file_path']}`")
    st.info("后续将支持从季度跟踪表跳转到对应生态公司池，并同步公司研究状态变化。")
    st.info("后续将支持从每日科技投资日报中自动提取重要事件，汇总到季度跟踪表。")
    st.info("后续将支持从季度跟踪表选择重点公司或一级项目，并进入 Valuation Cockpit 进行估值与尽调。")

    if tracking_overview["status"] != "已读取":
        st.warning("季度跟踪总览待建设。")
    elif tracking_overview.get("public") is not False:
        st.warning("季度跟踪总览文件应设置 frontmatter：public: false")

    tracking_cols = st.columns(2)
    for index, tracking in enumerate(trackings):
        with tracking_cols[index % 2]:
            with st.container(border=True):
                st.subheader(str(tracking["name"]))
                st.caption(str(tracking["status"]))
                st.write(f"所属战略生态：`{tracking['ecosystem']}`")
                st.write(f"当前季度：`{tracking.get('current_quarter') or '待补充'}`")
                st.write(f"Obsidian 文件：`{tracking['file_path']}`")
                st.write(f"对应公司池：`{tracking['ecosystem']}公司池`")
                public_label = "未标明" if tracking.get("public") is None else str(tracking.get("public")).lower()
                st.write(f"`public`: `{public_label}`")

                if tracking["status"] != "已读取":
                    st.warning("待建设")
                    continue
                if tracking.get("public") is not False:
                    st.warning("该内部研究文件应设置 frontmatter：public: false")

                detail_tabs = st.tabs(["关键指标", "公司池变化", "一级项目变化", "风险变化", "任务复盘", "下季度重点", "原文预览"])
                with detail_tabs[0]:
                    key_indicators = tracking.get("key_indicators") or []
                    if key_indicators:
                        st.dataframe(pd.DataFrame(key_indicators), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂未解析到关键指标。")
                with detail_tabs[1]:
                    company_changes = tracking.get("company_changes") or []
                    if company_changes:
                        st.dataframe(pd.DataFrame(company_changes), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂未解析到公司池变化。")
                with detail_tabs[2]:
                    project_changes = tracking.get("project_changes") or []
                    if project_changes:
                        st.dataframe(pd.DataFrame(project_changes), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂未解析到一级项目变化。")
                with detail_tabs[3]:
                    risk_changes = tracking.get("risk_changes") or []
                    if risk_changes:
                        st.dataframe(pd.DataFrame(risk_changes), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂未解析到风险变化。")
                with detail_tabs[4]:
                    task_review = tracking.get("research_task_review") or []
                    if task_review:
                        st.dataframe(pd.DataFrame(task_review), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂未解析到研究任务复盘。")
                with detail_tabs[5]:
                    focus = tracking.get("next_quarter_focus") or []
                    st.markdown("\n".join(f"- {item}" for item in focus) if focus else "暂无内容。")
                with detail_tabs[6]:
                    st.text_area(
                        "季度跟踪原文预览",
                        str(tracking.get("raw_markdown") or ""),
                        height=260,
                        key=f"quarterly_tracking_preview_{tracking['ecosystem']}",
                    )

with overview_tab:
    ecosystems = load_ecosystems()

    selected_title = None
    cols = st.columns(3)
    for index, ecosystem in enumerate(ecosystems):
        with cols[index % 3]:
            with st.container(border=True):
                st.subheader(ecosystem.title)
                st.caption(ecosystem.status)
                st.write(f"Obsidian 文件：`{ecosystem.path}`")
                public_label = "未标明" if ecosystem.public is None else str(ecosystem.public).lower()
                st.write(f"`public`: `{public_label}`")
                if ecosystem.exists:
                    section_count = len(ecosystem.sections)
                    st.write(f"已解析章节：{section_count}")
                    if st.button("查看详情", key=f"open_{ecosystem.title}"):
                        selected_title = ecosystem.title
                else:
                    st.warning("未找到 Obsidian 源文件")

    if selected_title is None:
        selected_title = st.session_state.get("selected_ecosystem_title")
    else:
        st.session_state["selected_ecosystem_title"] = selected_title

    st.divider()

    if selected_title:
        detail = load_ecosystem(selected_title)
        st.header(detail.title)
        st.write(f"状态：**{detail.status}**")
        st.write(f"Obsidian 文件路径：`{detail.path}`")

        if not detail.exists:
            st.error("未找到该战略生态的 Obsidian 文件。")
            st.stop()

        if detail.public is not False:
            st.warning("该内部研究文件应设置 frontmatter：public: false")

        section_order = list(SECTION_ALIASES.keys())
        tabs = st.tabs(section_order + ["关联公司 / 项目", "原文预览"])
        for tab, section_name in zip(tabs[:-1], section_order):
            with tab:
                content = detail.sections.get(section_name)
                if content:
                    st.markdown(content)
                else:
                    st.info("该章节尚未解析到内容。")

        with tabs[-2]:
            ecosystem_rows = (
                (company_database_linkage.get("matches") or {})
                .get(selected_title, {})
                .get("matched_companies", [])
            )
            if ecosystem_rows:
                st.dataframe(
                    pd.DataFrame([ecosystem_detail_link_row(row) for row in ecosystem_rows]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("暂未匹配到关联公司 / 项目。")

        with tabs[-1]:
            st.text_area("原文预览", detail.raw_preview, height=360)
    else:
        st.info("请选择一个战略生态查看详情。")
