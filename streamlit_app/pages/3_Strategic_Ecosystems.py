import pandas as pd
import streamlit as st

from app.services.ecosystem_loader import (
    SECTION_ALIASES,
    load_ecosystem,
    load_ecosystem_cross_map,
    load_ecosystems,
)


st.set_page_config(page_title="战略生态 | Rachel Capital OS", layout="wide")

st.title("战略生态")
st.caption("本地 Obsidian 研究文件读取视图，仅用于 localhost 内部研究管理。")

overview_tab, cross_map_tab = st.tabs(["七大战略生态", "生态交叉关系"])

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
        tabs = st.tabs(section_order + ["原文预览"])
        for tab, section_name in zip(tabs[:-1], section_order):
            with tab:
                content = detail.sections.get(section_name)
                if content:
                    st.markdown(content)
                else:
                    st.info("该章节尚未解析到内容。")

        with tabs[-1]:
            st.text_area("原文预览", detail.raw_preview, height=360)
    else:
        st.info("请选择一个战略生态查看详情。")
