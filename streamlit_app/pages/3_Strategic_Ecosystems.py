import streamlit as st

from app.services.ecosystem_loader import SECTION_ALIASES, load_ecosystem, load_ecosystems


st.set_page_config(page_title="战略生态 | Rachel Capital OS", layout="wide")

st.title("战略生态")
st.caption("本地 Obsidian 研究文件读取视图，仅用于 localhost 内部研究管理。")

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
