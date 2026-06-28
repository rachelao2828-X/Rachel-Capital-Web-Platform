import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.valuation_engine.document_parser import parse_uploaded_document
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import (
    write_listed_memo,
    write_private_market_document_analysis,
    write_private_market_document_valuation_framework,
    write_private_market_memo,
)
from app.services.valuation_engine.model_registry import (
    ASSET_ATTRIBUTES,
    ECOSYSTEM_OPTIONS,
    EXIT_PATHS,
    FINANCING_ROUNDS,
    LISTED_MARKETS,
    LISTED_PROFIT_GROWTH,
    LISTED_REVENUE_GROWTH,
    PRIVATE_REVENUE_GROWTH,
    PRIVATE_TARGET_TYPES,
)
from app.services.valuation_engine.private_market import PrivateMarketProfile, analyze_private_market
from app.services.valuation_engine.private_market_extractor import extract_private_market_document


PRIVATE_MARKET_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "private_market"
PRIVATE_MARKET_EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted" / "private_market"


def default_vault_path() -> str:
    return os.getenv("OBSIDIAN_VAULT_PATH") or settings.obsidian_vault_path or "/Users/rachelao/Documents/Rachel Capital"


def render_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.write("无")
        return
    for item in items:
        st.write(f"- {item}")


def safe_upload_filename(file_name: str) -> str:
    path = Path(file_name)
    stem = re.sub(r"[\\/:*?\"<>|\s]+", "_", path.stem).strip("_") or "uploaded_project_document"
    suffix = path.suffix.lower() or ".pdf"
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{stem}{suffix}"


def save_private_market_upload(uploaded_file) -> Path:
    PRIVATE_MARKET_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PRIVATE_MARKET_UPLOAD_DIR / safe_upload_filename(uploaded_file.name)
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


def save_private_market_extraction(parsed_document: dict, extraction: dict) -> Path:
    PRIVATE_MARKET_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    source_stem = Path(parsed_document.get("file_name", "project_document")).stem
    safe_stem = re.sub(r"[\\/:*?\"<>|\s]+", "_", source_stem).strip("_") or "project_document"
    output_path = PRIVATE_MARKET_EXTRACTED_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_stem}.json"
    output_path.write_text(
        json.dumps({"parsed_document": parsed_document, "extraction": extraction}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def section_rows(section: dict, labels: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for key, label in labels.items():
        value = section.get(key, "")
        if isinstance(value, list):
            display = "、".join(str(item) for item in value) if value else "未披露"
        elif value is None or value == "":
            display = "未披露"
        else:
            display = str(value)
        rows.append({"字段": label, "提取结果": display})
    return rows


def render_section_expander(title: str, section: dict, labels: dict[str, str], expanded: bool = False) -> None:
    with st.expander(title, expanded=expanded):
        st.dataframe(section_rows(section, labels), use_container_width=True, hide_index=True)


def render_private_document_upload() -> None:
    st.subheader("项目资料上传与解析")
    st.warning("商业计划书、融资材料和项目资料通常包含敏感信息。当前功能仅建议在本地可信环境使用。上传文件只保存在本地私有目录，不进入 public_site。")
    uploaded_file = st.file_uploader(
        "上传 PDF、PPTX、DOCX 项目资料、商业计划书或可研报告",
        type=["pdf", "ppt", "pptx", "doc", "docx"],
        accept_multiple_files=False,
        key="private_market_document_upload",
    )

    if uploaded_file and st.button("读取并解析上传资料"):
        saved_path = save_private_market_upload(uploaded_file)
        parsed_document = parse_uploaded_document(saved_path)
        extraction = extract_private_market_document(parsed_document)
        extracted_path = save_private_market_extraction(parsed_document, extraction)
        st.session_state["private_document_saved_path"] = saved_path
        st.session_state["private_document_parsed"] = parsed_document
        st.session_state["private_document_extraction"] = extraction
        st.session_state["private_document_extracted_path"] = extracted_path

    parsed_document = st.session_state.get("private_document_parsed")
    extraction = st.session_state.get("private_document_extraction")
    saved_path = st.session_state.get("private_document_saved_path")
    extracted_path = st.session_state.get("private_document_extracted_path")
    if not parsed_document or not extraction:
        return

    if parsed_document.get("extraction_quality") == "failed":
        st.error("文件读取未能完成，请查看解析警告。")
    else:
        st.success("文件读取完成。")
    if saved_path:
        st.caption(f"上传文件保存路径：{saved_path}")
    if extracted_path:
        st.caption(f"解析中间结果保存路径：{extracted_path}")
    status_cols = st.columns(4)
    status_cols[0].metric("文件类型", parsed_document.get("file_type") or "未知")
    status_cols[1].metric("解析器", parsed_document.get("parser") or "未知")
    status_cols[2].metric("解析质量", parsed_document.get("extraction_quality") or "未知")
    status_cols[3].metric("表格数量", len(parsed_document.get("tables", [])))
    for warning in parsed_document.get("warnings", []):
        st.warning(warning)

    summary = extraction.get("project_basic_info", {})
    readiness = extraction.get("valuation_readiness", {})
    financing = extraction.get("financing_info", {})
    financial = extraction.get("financial_data", {})
    founder_team = extraction.get("founder_team", {})
    commercial_model = extraction.get("business_model", {})
    technology = extraction.get("technology_route", {})
    product_and_customers = extraction.get("products_and_customers", {})
    market = extraction.get("market_space", {})
    capacity_data = extraction.get("capacity_data", {})
    cost_structure = extraction.get("cost_structure", {})
    exit_path = extraction.get("exit_path", {})
    risks = extraction.get("risk_factors", {})

    st.subheader("项目摘要与初判")
    cols = st.columns(4)
    cols[0].metric("项目名称", summary.get("project_name") or "待确认")
    cols[1].metric("标的类型初判", summary.get("target_type_guess") or "待确认")
    cols[2].metric("Rachel 战略生态", summary.get("rachel_ecosystem_guess") or "待确认")
    cols[3].metric("估值置信度", readiness.get("valuation_confidence_level") or "待确认")
    st.write(summary.get("one_sentence_summary") or "未提取到一句话摘要。")

    render_section_expander(
        "创始团队信息",
        founder_team,
        {
            "founders": "创始人",
            "co_founders": "联合创始人",
            "core_executives": "核心高管",
            "technical_lead": "技术负责人",
            "business_lead": "商业负责人",
            "finance_lead": "财务负责人",
            "advisors_or_board": "董事会 / 顾问",
            "education_background": "高校 / 教育背景",
            "industry_experience": "产业经验",
            "entrepreneurial_experience": "创业经历",
            "research_background": "科研 / 论文 / 专利背景",
            "big_company_background": "大厂背景",
            "industrial_resource_background": "产业资源背景",
            "fundraising_experience": "融资经验",
            "team_completeness": "团队完整度",
            "team_gaps": "团队短板",
            "key_person_dependency": "关键人依赖",
            "team_risks": "团队风险",
        },
        expanded=True,
    )

    render_section_expander(
        "商业模式",
        commercial_model,
        {
            "revenue_sources": "收入来源",
            "customer_type": "客户类型",
            "payment_model": "付费模式",
            "delivery_model": "交付方式",
            "is_project_based": "是否项目制",
            "is_productized": "是否产品化",
            "is_platform_based": "是否平台型",
            "is_asset_or_resource_driven": "是否资源 / 资产驱动",
            "depends_on_government_or_key_customers": "是否依赖政府订单或大客户",
        },
    )

    render_section_expander(
        "产品与客户",
        product_and_customers,
        {
            "products": "主要产品",
            "product_form": "产品形态",
            "customer_type": "客户类型",
            "signed_customers": "已签客户",
            "intended_customers": "意向客户",
            "orders": "订单情况",
            "contracts": "合同情况",
            "customer_concentration": "客户集中度",
            "repurchase": "复购情况",
            "channels": "渠道情况",
        },
    )

    col_tech, col_market = st.columns(2)
    with col_tech:
        render_section_expander(
            "技术路线",
            technology,
            {
                "core_technology": "核心技术",
                "patents": "专利",
                "technical_maturity": "技术成熟度",
                "competitive_advantage": "技术壁垒 / 竞争优势",
                "key_dependencies": "关键技术依赖",
            },
        )
    with col_market:
        render_section_expander(
            "市场空间",
            market,
            {
                "market_size": "市场空间",
                "market_growth": "市场增速 / 景气度",
                "competitors": "竞争格局",
                "comparable_listed_companies": "可比上市公司",
                "comparable_private_companies": "可比未上市公司",
            },
        )

    col_financing, col_financial = st.columns(2)
    with col_financing:
        st.subheader("融资信息提取表")
        st.dataframe(
            section_rows(
                financing,
                {
                    "is_fundraising": "是否融资",
                    "financing_stage": "融资阶段",
                    "pre_money_valuation": "投前估值",
                    "post_money_valuation": "投后估值",
                    "financing_amount": "融资金额",
                    "equity_offered": "出让股权",
                    "previous_round": "上一轮融资",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
    with col_financial:
        st.subheader("财务数据提取表")
        st.dataframe(
            section_rows(
                financial,
                {
                    "historical_revenue": "历史收入",
                    "forecast_revenue": "预测收入",
                    "gross_margin": "毛利率",
                    "net_margin": "净利率",
                    "ebitda": "EBITDA",
                    "capex": "资本开支",
                    "opex": "运营成本",
                    "cash_flow": "现金流",
                    "payback_period": "回收期",
                    "break_even_time": "盈亏平衡时间",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )

    col_cost, col_exit = st.columns(2)
    with col_cost:
        render_section_expander(
            "产能数据",
            capacity_data,
            {
                "designed_capacity": "设计产能",
                "current_capacity": "当前产能",
                "capacity_expansion_plan": "产能爬坡 / 扩产计划",
                "capacity_utilization": "产能利用率",
                "construction_period": "建设周期",
                "unit_price": "单位售价",
                "unit_cost": "单位成本",
                "production_base": "生产基地",
                "equipment_investment": "设备投入",
                "production_lines": "产线数量",
            },
        )
        render_section_expander(
            "成本结构",
            cost_structure,
                {
                    "capex": "CAPEX",
                    "opex": "OPEX",
                    "raw_material_cost": "原材料成本",
                    "energy_cost": "能耗成本",
                    "labor_cost": "人工成本",
                    "depreciation": "设备折旧",
                    "maintenance_cost": "运维成本",
                    "environmental_cost": "环保成本",
                    "compliance_cost": "合规成本",
                    "unit_economics": "单位经济模型",
                },
        )
    with col_exit:
        render_section_expander(
            "退出路径",
            exit_path,
            {
                "ipo": "IPO",
                "ma": "并购",
                "dividend_recovery": "分红回收",
                "asset_sale": "资产出售",
                "equity_transfer": "股权转让",
                "strategic_acquisition": "产业方收购",
                "expected_exit_time": "退出时间预期",
                "comparable_exit_cases": "可比退出案例",
            },
        )

    render_section_expander(
        "风险因素",
        risks,
        {
            "technology_risk": "技术风险",
            "market_risk": "市场风险",
            "customer_risk": "客户风险",
            "policy_risk": "政策风险",
            "financing_risk": "融资风险",
            "execution_risk": "执行 / 产能爬坡风险",
            "team_risk": "团队风险",
            "key_person_risk": "关键人风险",
            "data_reliability_risk": "数据真实性风险",
            "compliance_risk": "合规风险",
        },
    )

    render_section_expander(
        "估值可用性",
        readiness,
        {
            "recommended_models": "推荐估值模型",
            "usable_data": "当前可用数据",
            "missing_data": "缺失数据清单",
            "questions_for_company": "建议向项目方追问的问题",
            "data_confidence_level": "数据可信度",
            "valuation_confidence_level": "估值置信度",
            "ready_for_preliminary_valuation": "是否适合进入初步估值",
            "unavailable_models": "暂不可用模型",
        },
        expanded=True,
    )

    with st.expander("数据可信度标记", expanded=False):
        st.dataframe(extraction.get("field_assessments", []), use_container_width=True, hide_index=True)

    col_models, col_missing, col_questions = st.columns(3)
    with col_models:
        render_list("推荐估值模型", readiness.get("recommended_models", []))
        render_list("暂不可用模型", readiness.get("unavailable_models", []))
    with col_missing:
        render_list("当前可用数据", readiness.get("usable_data", []))
        render_list("缺失数据清单", readiness.get("missing_data", []))
    with col_questions:
        render_list("建议向项目方追问的问题", readiness.get("questions_for_company", []))

    st.subheader("生成 Obsidian 草稿")
    vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="private_document_vault_path")
    col_doc, col_framework = st.columns(2)
    with col_doc:
        st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "一级市场项目资料解析"))
        if st.button("生成 Obsidian 项目资料解析报告"):
            try:
                output_path = write_private_market_document_analysis(extraction, parsed_document, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")
    with col_framework:
        st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "未上市一级市场"))
        if st.button("生成 Obsidian 估值框架草稿"):
            try:
                output_path = write_private_market_document_valuation_framework(extraction, parsed_document, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")


def render_listed_result() -> None:
    profile = st.session_state.get("listed_profile")
    result = st.session_state.get("listed_result")
    if not profile or not result:
        st.info("填写已上市公司信息后，点击“生成已上市公司估值框架”。")
        return

    st.subheader("标的画像")
    cols = st.columns(3)
    cols[0].metric("市场", profile.market)
    cols[1].metric("资产属性", profile.asset_attribute)
    cols[2].metric("研究动作建议", result.research_action)
    render_list("公司画像识别", result.portrait)

    st.subheader("系统推荐估值模型")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        render_list("主模型", result.primary_models)
    with col_b:
        render_list("辅助模型", result.auxiliary_models)
    with col_c:
        render_list("参考模型", result.reference_models)
    with col_d:
        render_list("不建议使用", result.unsuitable_models)

    st.subheader("多模型适用性对比")
    st.dataframe(result.comparison_table, use_container_width=True, hide_index=True)

    with st.expander("模型说明与判断逻辑"):
        st.write("系统根据盈利状态、收入增长、利润增长、资产属性、现金流、周期属性、SOTP 适配度和困境修复状态选择模型。")
        st.write("输出仅作为研究框架，不输出操作结论。")

    st.subheader("当前需要补充的数据")
    render_list("数据清单", result.data_requirements)

    st.subheader("初步估值框架")
    render_list("框架", result.valuation_framework)

    st.subheader("风险与不确定性")
    render_list("风险", result.risks)

    st.subheader("生成 Obsidian 估值备忘录草稿")
    vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="listed_vault_path")
    st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "已上市公司"))
    if st.button("生成已上市公司估值备忘录草稿"):
        try:
            output_path = write_listed_memo(profile, result, vault_path)
        except OSError as exc:
            st.error(f"生成失败：{exc}")
        else:
            st.success(f"已生成：{output_path}")
            st.code(str(output_path), language="text")


def render_private_result() -> None:
    profile = st.session_state.get("private_profile")
    result = st.session_state.get("private_result")
    if not profile or not result:
        st.info("填写未上市 / 一级市场信息后，点击“生成未上市 / 一级市场估值框架”。")
        return

    st.subheader("标的画像")
    cols = st.columns(4)
    cols[0].metric("主分类", result.classification.primary_type)
    cols[1].metric("辅助分类", "、".join(result.classification.secondary_types) if result.classification.secondary_types else "无")
    cols[2].metric("退出路径", profile.exit_path)
    cols[3].metric("研究动作建议", result.research_action)
    render_list("画像", result.portrait)

    st.subheader("判断理由")
    render_list("理由", result.classification.reasons)

    st.subheader("推荐估值模型")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        render_list("主模型", result.primary_models)
    with col_b:
        render_list("辅助模型", result.auxiliary_models)
    with col_c:
        render_list("参考模型", result.reference_models)
    with col_d:
        render_list("不建议使用", result.unsuitable_models)

    st.subheader("多模型适用性对比")
    display_rows = [
        {
            "模型": row["模型"],
            "适用度": row["适用度"],
            "适用原因": row["适用原因"],
            "必需数据": row["必需数据"],
            "输出结果": row["输出结果"],
            "权重建议": row["权重建议"],
        }
        for row in result.comparison_table
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)

    st.subheader("必须加入的折扣或敏感性因素")
    render_list("因素", result.required_adjustments)

    with st.expander("模型说明与判断逻辑"):
        st.write("系统先识别未上市成长公司、一级市场融资标的、项目公司 / SPV、资产型项目，再根据主分类和辅助分类组合模型。")
        st.write("折扣、敏感性和退出路径是非公开市场估值框架的核心部分。")

    st.subheader("当前需要补充的数据")
    render_list("数据清单", result.data_requirements)

    st.subheader("初步估值框架")
    render_list("框架", result.valuation_framework)

    st.subheader("风险与不确定性")
    render_list("风险", result.risks)

    st.subheader("生成 Obsidian 估值备忘录草稿")
    vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="private_vault_path")
    st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "未上市一级市场"))
    if st.button("生成未上市 / 一级市场估值备忘录草稿"):
        try:
            output_path = write_private_market_memo(profile, result, vault_path)
        except OSError as exc:
            st.error(f"生成失败：{exc}")
        else:
            st.success(f"已生成：{output_path}")
            st.code(str(output_path), language="text")


st.set_page_config(page_title="估值驾驶舱 | Rachel Capital OS Platform", layout="wide")
st.title("Rachel 估值驾驶舱")
st.caption("Valuation Cockpit V0.2：已上市公司与未上市 / 一级市场估值分离，仅用于本地研究框架。")

listed_tab, private_tab = st.tabs(["已上市公司估值", "未上市 / 一级市场估值"])

with listed_tab:
    st.header("已上市公司估值")
    st.caption("用于 A股、港股、美股、港股通等公开市场标的。核心问题：公开市场当前市值是否处于合理区间。")
    with st.form("listed_company_form"):
        st.subheader("标的基本信息")
        col_1, col_2, col_3, col_4 = st.columns(4)
        stock_name = col_1.text_input("股票名称", placeholder="例如：中国船舶")
        ticker = col_2.text_input("股票代码", placeholder="例如：600150.SH")
        market = col_3.selectbox("市场", LISTED_MARKETS)
        industry = col_4.text_input("所属行业", placeholder="例如：船舶制造")
        ecosystem = st.selectbox("所属 Rachel 战略生态", ECOSYSTEM_OPTIONS, key="listed_ecosystem")

        st.subheader("公司特征")
        col_a, col_b, col_c = st.columns(3)
        is_profitable = col_a.checkbox("是否盈利", value=True)
        revenue_growth_status = col_b.selectbox("收入增长状态", LISTED_REVENUE_GROWTH)
        profit_growth_status = col_c.selectbox("利润增长状态", LISTED_PROFIT_GROWTH)

        col_d, col_e, col_f = st.columns(3)
        asset_attribute = col_d.selectbox("资产属性", ASSET_ATTRIBUTES)
        cash_flow_stability = col_e.selectbox("现金流稳定性", ["稳定", "一般", "不稳定"])
        is_strong_cycle = col_f.radio("是否强周期", ["否", "是"], horizontal=True) == "是"

        col_g, col_h = st.columns(2)
        is_sotp_suitable = col_g.radio("是否适合 SOTP", ["否", "是"], horizontal=True) == "是"
        is_turnaround = col_h.radio("是否处于困境反转", ["否", "是"], horizontal=True) == "是"

        listed_submit = st.form_submit_button("生成已上市公司估值框架")

    if listed_submit:
        if not stock_name.strip():
            st.error("请填写股票名称。")
        else:
            listed_profile = ListedCompanyProfile(
                stock_name=stock_name.strip(),
                ticker=ticker.strip(),
                market=market,
                industry=industry.strip(),
                ecosystem=ecosystem,
                is_profitable=is_profitable,
                revenue_growth_status=revenue_growth_status,
                profit_growth_status=profit_growth_status,
                asset_attribute=asset_attribute,
                cash_flow_stability=cash_flow_stability,
                is_strong_cycle=is_strong_cycle,
                is_sotp_suitable=is_sotp_suitable,
                is_turnaround=is_turnaround,
            )
            st.session_state["listed_profile"] = listed_profile
            st.session_state["listed_result"] = analyze_listed_company(listed_profile)

    render_listed_result()

with private_tab:
    st.header("未上市 / 一级市场估值")
    st.caption("用于未上市成长公司、融资交易、Pre-IPO、老股转让、项目公司 / SPV、资产型项目。")
    render_private_document_upload()
    st.divider()
    st.subheader("标的基本信息")
    col_1, col_2, col_3 = st.columns(3)
    target_name = col_1.text_input("标的名称", placeholder="例如：OpenAI 老股交易 / 信宜绿色算力中心")
    initial_type = col_2.selectbox("标的类型初选", PRIVATE_TARGET_TYPES)
    private_industry = col_3.text_input("所属行业", placeholder="例如：AI应用 / 绿色算力 / 资源回收")
    private_ecosystem = st.selectbox("所属 Rachel 战略生态", ECOSYSTEM_OPTIONS, key="private_ecosystem")

    st.subheader("交易 / 项目特征")
    col_a, col_b, col_c, col_d = st.columns(4)
    is_financing_or_transfer = col_a.checkbox("是否正在融资或老股转让")
    is_complete_company = col_b.checkbox("是否为完整公司主体", value=True)
    is_single_project_spv = col_c.checkbox("是否为单一项目 / SPV")
    is_asset_or_contract_based = col_d.checkbox("是否主要依赖资产、资源、牌照或合同")

    col_e, col_f, col_g, col_h = st.columns(4)
    has_revenue = col_e.checkbox("是否已有收入", value=True)
    is_private_profitable = col_f.checkbox("是否盈利")
    private_revenue_growth = col_g.selectbox("收入增长状态", PRIVATE_REVENUE_GROWTH)
    private_cash_flow_stable = col_h.checkbox("现金流是否稳定")
    exit_path = st.selectbox("退出路径", EXIT_PATHS)

    financing_round = pre_money = post_money = financing_amount = equity_sold = previous_round_valuation = previous_round_date = None
    if initial_type == "一级市场融资标的" or is_financing_or_transfer:
        st.subheader("一级市场专用字段")
        col_i, col_j, col_k, col_l = st.columns(4)
        financing_round = col_i.selectbox("本轮融资类型", FINANCING_ROUNDS)
        pre_money = col_j.text_input("投前估值")
        post_money = col_k.text_input("投后估值")
        financing_amount = col_l.text_input("本轮融资金额")
        col_m, col_n, col_o = st.columns(3)
        equity_sold = col_m.text_input("出让股权比例")
        previous_round_valuation = col_n.text_input("上一轮估值")
        previous_round_date = col_o.text_input("上一轮融资时间")

    project_total_investment = construction_period = expected_revenue = expected_gross_margin = expected_net_margin = annual_cash_flow = payback_period = government_subsidy = utilization_rate = None
    key_contract_signed = None
    if initial_type == "项目公司 / SPV" or is_single_project_spv:
        st.subheader("项目公司 / SPV 专用字段")
        col_p, col_q, col_r, col_s = st.columns(4)
        project_total_investment = col_p.text_input("项目总投资")
        construction_period = col_q.text_input("建设周期")
        expected_revenue = col_r.text_input("预计收入")
        expected_gross_margin = col_s.text_input("预计毛利率")
        col_t, col_u, col_v, col_w = st.columns(4)
        expected_net_margin = col_t.text_input("预计净利率")
        annual_cash_flow = col_u.text_input("年现金流")
        payback_period = col_v.text_input("回收期")
        government_subsidy = col_w.text_input("政府补贴")
        col_x, col_y = st.columns(2)
        key_contract_signed = col_x.checkbox("关键合同是否已签署")
        utilization_rate = col_y.text_input("产能利用率 / 上架率 / 负荷率")

    asset_type = book_value = replacement_cost = comparable_transaction_price = None
    asset_generates_cash_flow = asset_is_scarce = asset_is_tradeable = asset_has_long_contract = asset_has_policy_restriction = None
    if initial_type == "资产型项目" or is_asset_or_contract_based:
        st.subheader("资产型项目专用字段")
        col_z, col_aa, col_ab, col_ac = st.columns(4)
        asset_type = col_z.text_input("资产类型")
        book_value = col_aa.text_input("资产账面价值")
        replacement_cost = col_ab.text_input("重置成本")
        comparable_transaction_price = col_ac.text_input("可比交易价格")
        col_ad, col_ae, col_af, col_ag, col_ah = st.columns(5)
        asset_generates_cash_flow = col_ad.checkbox("是否产生现金流")
        asset_is_scarce = col_ae.checkbox("是否具备稀缺性")
        asset_is_tradeable = col_af.checkbox("是否可交易")
        asset_has_long_contract = col_ag.checkbox("是否有长期合同")
        asset_has_policy_restriction = col_ah.checkbox("是否有政策限制")

    private_submit = st.button("生成未上市 / 一级市场估值框架")

    if private_submit:
        if not target_name.strip():
            st.error("请填写标的名称。")
        else:
            private_profile = PrivateMarketProfile(
                target_name=target_name.strip(),
                initial_type=initial_type,
                industry=private_industry.strip(),
                ecosystem=private_ecosystem,
                is_financing_or_transfer=is_financing_or_transfer,
                is_complete_company=is_complete_company,
                is_single_project_spv=is_single_project_spv,
                is_asset_or_contract_based=is_asset_or_contract_based,
                has_revenue=has_revenue,
                is_profitable=is_private_profitable,
                revenue_growth_status=private_revenue_growth,
                cash_flow_stable=private_cash_flow_stable,
                exit_path=exit_path,
                financing_round=financing_round,
                pre_money_valuation=pre_money,
                post_money_valuation=post_money,
                financing_amount=financing_amount,
                equity_sold=equity_sold,
                previous_round_valuation=previous_round_valuation,
                previous_round_date=previous_round_date,
                project_total_investment=project_total_investment,
                construction_period=construction_period,
                expected_revenue=expected_revenue,
                expected_gross_margin=expected_gross_margin,
                expected_net_margin=expected_net_margin,
                annual_cash_flow=annual_cash_flow,
                payback_period=payback_period,
                government_subsidy=government_subsidy,
                key_contract_signed=key_contract_signed,
                utilization_rate=utilization_rate,
                asset_type=asset_type,
                book_value=book_value,
                replacement_cost=replacement_cost,
                comparable_transaction_price=comparable_transaction_price,
                asset_generates_cash_flow=asset_generates_cash_flow,
                asset_is_scarce=asset_is_scarce,
                asset_is_tradeable=asset_is_tradeable,
                asset_has_long_contract=asset_has_long_contract,
                asset_has_policy_restriction=asset_has_policy_restriction,
            )
            st.session_state["private_profile"] = private_profile
            st.session_state["private_result"] = analyze_private_market(private_profile)

    render_private_result()

st.divider()
st.caption("本页面仅用于 Rachel Capital OS 本地研究与估值框架准备，不连接交易系统，不生成操作结论。")
