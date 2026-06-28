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
from app.services.valuation_engine.assumption_manager import (
    ASSUMPTION_GROUP_LABELS,
    assumption_counts,
    build_assumption_table,
    finalize_assumption_data,
    update_group_from_rows,
)
from app.services.valuation_engine.document_parser import parse_uploaded_document
from app.services.valuation_engine.financial_model_parser import parse_financial_model
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import (
    write_basic_valuation_calculation_report,
    write_assumption_confirmation_report,
    write_due_diligence_questions,
    write_listed_memo,
    write_multi_model_valuation_report,
    write_private_market_project_card,
    write_private_market_investment_memo,
    write_private_market_document_analysis,
    write_private_market_document_valuation_framework,
    write_private_market_financial_model_analysis,
    write_private_market_memo,
    write_project_tracking_tasks,
    update_private_market_project_watchlist,
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
from app.services.valuation_engine.investment_memo_builder import build_private_market_investment_memo
from app.services.valuation_engine.private_market_autofill import (
    build_private_market_autofill_from_document,
    build_private_market_autofill_from_financial_model,
)
from app.services.valuation_engine.private_market_extractor import extract_private_market_document
from app.services.valuation_engine.multi_model_valuation import (
    display_money,
    run_multi_model_comparison,
)
from app.services.valuation_engine.project_tracker import (
    PROJECT_STATUS_OPTIONS,
    WATCHLIST_STATUS_LABELS,
    WATCHLIST_STATUS_OPTIONS,
    build_project_tracking_record,
    suggest_next_review_date,
)
from app.services.valuation_engine.valuation_calculator import run_basic_private_market_valuation


PRIVATE_MARKET_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "private_market"
PRIVATE_MARKET_EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted" / "private_market"
PRIVATE_MARKET_FINANCIAL_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "private_market_financials"
PRIVATE_MARKET_FINANCIAL_EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted" / "private_market_financials"
PRIVATE_MARKET_CASES_DIR = PROJECT_ROOT / "data" / "private_market_cases"

PRIVATE_AUTOFILL_WIDGET_KEYS = {
    "target_name": "private_target_name",
    "initial_type": "private_initial_type",
    "industry": "private_industry",
    "ecosystem": "private_ecosystem",
    "is_financing_or_transfer": "private_is_financing_or_transfer",
    "is_complete_company": "private_is_complete_company",
    "is_single_project_spv": "private_is_single_project_spv",
    "is_asset_or_contract_based": "private_is_asset_or_contract_based",
    "has_revenue": "private_has_revenue",
    "is_profitable": "private_is_profitable",
    "revenue_growth_status": "private_revenue_growth",
    "cash_flow_stable": "private_cash_flow_stable",
    "exit_path": "private_exit_path",
    "financing_round": "private_financing_round",
    "pre_money_valuation": "private_pre_money",
    "post_money_valuation": "private_post_money",
    "financing_amount": "private_financing_amount",
    "equity_sold": "private_equity_sold",
    "previous_round_valuation": "private_previous_round_valuation",
    "previous_round_date": "private_previous_round_date",
    "project_total_investment": "private_project_total_investment",
    "construction_period": "private_construction_period",
    "expected_revenue": "private_expected_revenue",
    "expected_gross_margin": "private_expected_gross_margin",
    "expected_net_margin": "private_expected_net_margin",
    "annual_cash_flow": "private_annual_cash_flow",
    "payback_period": "private_payback_period",
    "government_subsidy": "private_government_subsidy",
    "key_contract_signed": "private_key_contract_signed",
    "utilization_rate": "private_utilization_rate",
    "asset_type": "private_asset_type",
    "book_value": "private_book_value",
    "replacement_cost": "private_replacement_cost",
    "comparable_transaction_price": "private_comparable_transaction_price",
    "asset_generates_cash_flow": "private_asset_generates_cash_flow",
    "asset_is_scarce": "private_asset_is_scarce",
    "asset_is_tradeable": "private_asset_is_tradeable",
    "asset_has_long_contract": "private_asset_has_long_contract",
    "asset_has_policy_restriction": "private_asset_has_policy_restriction",
}

PRIVATE_AUTOFILL_LABELS = {
    "target_name": "标的名称",
    "initial_type": "标的类型初选",
    "industry": "所属行业",
    "ecosystem": "所属 Rachel 战略生态",
    "is_financing_or_transfer": "是否正在融资或老股转让",
    "is_complete_company": "是否为完整公司主体",
    "is_single_project_spv": "是否为单一项目 / SPV",
    "is_asset_or_contract_based": "是否主要依赖资产、资源、牌照或合同",
    "has_revenue": "是否已有收入",
    "is_profitable": "是否盈利",
    "revenue_growth_status": "收入增长状态",
    "cash_flow_stable": "现金流是否稳定",
    "exit_path": "退出路径",
    "financing_round": "本轮融资类型",
    "pre_money_valuation": "投前估值",
    "post_money_valuation": "投后估值",
    "financing_amount": "本轮融资金额",
    "equity_sold": "出让股权比例",
    "previous_round_valuation": "上一轮估值",
    "previous_round_date": "上一轮融资时间",
    "project_total_investment": "项目总投资",
    "construction_period": "建设周期",
    "expected_revenue": "预计收入",
    "expected_gross_margin": "预计毛利率",
    "expected_net_margin": "预计净利率",
    "annual_cash_flow": "年现金流",
    "payback_period": "回收期",
    "government_subsidy": "政府补贴",
    "key_contract_signed": "关键合同是否已签署",
    "utilization_rate": "产能利用率 / 上架率 / 负荷率",
    "asset_type": "资产类型",
    "book_value": "资产账面价值",
    "replacement_cost": "重置成本",
    "comparable_transaction_price": "可比交易价格",
    "asset_generates_cash_flow": "是否产生现金流",
    "asset_is_scarce": "是否具备稀缺性",
    "asset_is_tradeable": "是否可交易",
    "asset_has_long_contract": "是否有长期合同",
    "asset_has_policy_restriction": "是否有政策限制",
}


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


def save_private_market_financial_upload(uploaded_file) -> Path:
    PRIVATE_MARKET_FINANCIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PRIVATE_MARKET_FINANCIAL_UPLOAD_DIR / safe_upload_filename(uploaded_file.name)
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


def save_private_market_financial_extraction(financial_model: dict) -> Path:
    PRIVATE_MARKET_FINANCIAL_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    source_stem = Path(financial_model.get("file_name", "financial_model")).stem
    safe_stem = re.sub(r"[\\/:*?\"<>|\s]+", "_", source_stem).strip("_") or "financial_model"
    output_path = PRIVATE_MARKET_FINANCIAL_EXTRACTED_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_stem}.json"
    output_path.write_text(json.dumps(financial_model, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_assumption_confirmation(assumption_data: dict) -> Path:
    PRIVATE_MARKET_CASES_DIR.mkdir(parents=True, exist_ok=True)
    target_name = assumption_data.get("target_name") or "未命名项目"
    safe_name = re.sub(r"[\\/:*?\"<>|\s]+", "_", target_name).strip("_") or "未命名项目"
    output_path = PRIVATE_MARKET_CASES_DIR / f"{safe_name}_{datetime.now().date().isoformat()}_关键假设确认.json"
    output_path.write_text(json.dumps(assumption_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_basic_valuation_result(valuation_result: dict) -> Path:
    PRIVATE_MARKET_CASES_DIR.mkdir(parents=True, exist_ok=True)
    target_name = valuation_result.get("target_name") or "未命名项目"
    safe_name = re.sub(r"[\\/:*?\"<>|\s]+", "_", target_name).strip("_") or "未命名项目"
    output_path = PRIVATE_MARKET_CASES_DIR / f"{safe_name}_{datetime.now().date().isoformat()}_基础估值计算.json"
    output_path.write_text(json.dumps(valuation_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_multi_model_valuation_result(multi_model_result: dict) -> Path:
    PRIVATE_MARKET_CASES_DIR.mkdir(parents=True, exist_ok=True)
    target_name = multi_model_result.get("target_name") or "未命名项目"
    safe_name = re.sub(r"[\\/:*?\"<>|\s]+", "_", target_name).strip("_") or "未命名项目"
    output_path = PRIVATE_MARKET_CASES_DIR / f"{safe_name}_{datetime.now().date().isoformat()}_多模型估值对比.json"
    output_path.write_text(json.dumps(multi_model_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_investment_memo_result(memo_data: dict) -> Path:
    PRIVATE_MARKET_CASES_DIR.mkdir(parents=True, exist_ok=True)
    target_name = memo_data.get("target_name") or "未命名项目"
    safe_name = re.sub(r"[\\/:*?\"<>|\s]+", "_", target_name).strip("_") or "未命名项目"
    output_path = PRIVATE_MARKET_CASES_DIR / f"{safe_name}_{datetime.now().date().isoformat()}_投资备忘录整合.json"
    output_path.write_text(json.dumps(memo_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_project_tracking_result(tracking_record: dict) -> Path:
    PRIVATE_MARKET_CASES_DIR.mkdir(parents=True, exist_ok=True)
    target_name = tracking_record.get("target_name") or "未命名项目"
    safe_name = re.sub(r"[\\/:*?\"<>|\s]+", "_", target_name).strip("_") or "未命名项目"
    output_path = PRIVATE_MARKET_CASES_DIR / f"{safe_name}_{datetime.now().date().isoformat()}_项目跟踪记录.json"
    output_path.write_text(json.dumps(tracking_record, ensure_ascii=False, indent=2), encoding="utf-8")
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


def project_name_from_current_analysis() -> str:
    extraction = st.session_state.get("private_document_extraction") or {}
    summary = extraction.get("project_basic_info", {})
    return summary.get("project_name") or summary.get("company_name") or "未命名项目"


def apply_private_market_autofill(values: dict, source: str) -> None:
    applied_labels = []
    for field, value in values.items():
        widget_key = PRIVATE_AUTOFILL_WIDGET_KEYS.get(field)
        if not widget_key:
            continue
        st.session_state[widget_key] = value
        applied_labels.append(PRIVATE_AUTOFILL_LABELS.get(field, field))
    if applied_labels:
        st.session_state["private_autofill_message"] = f"{source}已自动回填：" + "、".join(applied_labels)


def render_private_autofill_message() -> None:
    message = st.session_state.get("private_autofill_message")
    if message:
        st.success(message)
        st.caption("自动回填结果来自上传资料解析，建议人工复核后再生成估值框架。")


def ensure_private_form_defaults() -> None:
    defaults = {
        "private_initial_type": PRIVATE_TARGET_TYPES[0],
        "private_ecosystem": ECOSYSTEM_OPTIONS[0],
        "private_is_financing_or_transfer": False,
        "private_is_complete_company": True,
        "private_is_single_project_spv": False,
        "private_is_asset_or_contract_based": False,
        "private_has_revenue": True,
        "private_is_profitable": False,
        "private_revenue_growth": PRIVATE_REVENUE_GROWTH[0],
        "private_cash_flow_stable": False,
        "private_exit_path": EXIT_PATHS[0],
        "private_financing_round": FINANCING_ROUNDS[0],
        "private_key_contract_signed": False,
        "private_asset_generates_cash_flow": False,
        "private_asset_is_scarce": False,
        "private_asset_is_tradeable": False,
        "private_asset_has_long_contract": False,
        "private_asset_has_policy_restriction": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_financial_model_upload() -> None:
    st.subheader("Excel / 财务模型上传与解析")
    st.warning("财务模型、预测表和审计资料通常包含敏感信息。当前功能仅建议在本地可信环境使用。上传文件只保存在本地私有目录，不进入 public_site。")
    uploaded_file = st.file_uploader(
        "上传 XLSX、CSV 财务模型、预测表或项目测算表",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
        key="private_market_financial_upload",
    )

    if uploaded_file and st.button("读取并解析财务模型"):
        saved_path = save_private_market_financial_upload(uploaded_file)
        financial_model = parse_financial_model(saved_path)
        extracted_path = save_private_market_financial_extraction(financial_model)
        st.session_state["private_financial_saved_path"] = saved_path
        st.session_state["private_financial_model"] = financial_model
        st.session_state["private_financial_extracted_path"] = extracted_path
        apply_private_market_autofill(build_private_market_autofill_from_financial_model(financial_model), "财务模型")

    financial_model = st.session_state.get("private_financial_model")
    saved_path = st.session_state.get("private_financial_saved_path")
    extracted_path = st.session_state.get("private_financial_extracted_path")
    if not financial_model:
        return

    if financial_model.get("extraction_quality") == "failed":
        st.error("财务模型读取未能完成，请查看解析警告。")
    else:
        st.success("财务模型读取完成。")
    if saved_path:
        st.caption(f"上传文件保存路径：{saved_path}")
    if extracted_path:
        st.caption(f"解析中间结果保存路径：{extracted_path}")

    status_cols = st.columns(4)
    status_cols[0].metric("文件类型", financial_model.get("file_type") or "未知")
    status_cols[1].metric("解析器", financial_model.get("parser") or "未知")
    status_cols[2].metric("解析质量", financial_model.get("extraction_quality") or "未知")
    status_cols[3].metric("Sheet 数量", len(financial_model.get("sheets", [])))
    for warning in financial_model.get("warnings", []):
        st.warning(warning)

    extracted = financial_model.get("extracted_financial_data", {})
    sheets = financial_model.get("sheets", [])
    sections = financial_model.get("detected_financial_sections", {})

    with st.expander("Sheet 列表", expanded=True):
        st.dataframe(sheets, use_container_width=True, hide_index=True)

    with st.expander("每张 Sheet 前 20 行预览", expanded=False):
        for sheet_name, rows in financial_model.get("raw_preview", {}).items():
            st.markdown(f"**{sheet_name}**")
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with st.expander("自动识别的财务表类型", expanded=True):
        section_rows_display = [
            {
                "财务表类型": section,
                "匹配 Sheet": "、".join(item.get("sheet_name", "") for item in matches) if matches else "未识别",
                "关键词": "、".join(item.get("matched_keywords", "") for item in matches) if matches else "",
            }
            for section, matches in sections.items()
        ]
        st.dataframe(section_rows_display, use_container_width=True, hide_index=True)

    with st.expander("提取出的关键财务字段", expanded=True):
        st.dataframe(extracted.get("field_assessments", []), use_container_width=True, hide_index=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        render_list("缺失财务数据清单", extracted.get("missing_financial_data", []))
    with col_b:
        render_list("需要用户确认的数据", extracted.get("requires_user_confirmation", []))
    with col_c:
        render_list("可用于估值的字段", extracted.get("usable_financial_data", []))
        render_list("当前可支持的估值模型", extracted.get("supported_valuation_models", []))

    render_list("建议补充的财务资料", extracted.get("recommended_supplemental_materials", []))

    if st.session_state.get("private_document_extraction"):
        st.info("财务模型补充结果：Excel / 财务模型用于补充项目资料中缺失的财务、产能、成本、现金流、IRR 和敏感性数据。若文本资料与 Excel 数据冲突，请优先人工核验。")

    st.subheader("生成 Obsidian 财务模型解析报告")
    vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="private_financial_vault_path")
    st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "一级市场财务模型解析"))
    if st.button("生成 Obsidian 财务模型解析报告"):
        try:
            output_path = write_private_market_financial_model_analysis(financial_model, vault_path, project_name_from_current_analysis())
        except OSError as exc:
            st.error(f"生成失败：{exc}")
        else:
            st.success(f"已生成：{output_path}")
            st.code(str(output_path), language="text")


def current_assumption_sources() -> tuple[dict | None, dict | None]:
    document_extraction = st.session_state.get("private_document_extraction")
    parsed_document = st.session_state.get("private_document_parsed")
    if document_extraction and parsed_document:
        document_extraction = {**document_extraction, "_source_file": parsed_document.get("file_name", "")}
    return document_extraction, st.session_state.get("private_financial_model")


def render_assumption_confirmation_page() -> None:
    st.subheader("关键假设确认页")
    st.warning("BP、财务模型和项目资料中的数据通常来自项目方预测，可能存在乐观假设。请在进入自动估值计算前确认关键收入、成本、现金流、CAPEX、估值、团队和退出路径假设。")
    document_extraction, financial_model = current_assumption_sources()
    if not document_extraction and not financial_model:
        st.info("上传并解析项目资料或 Excel / 财务模型后，这里会生成关键假设确认表。")
        return

    if st.button("生成 / 刷新关键假设表"):
        st.session_state["private_assumption_data"] = build_assumption_table(document_extraction, financial_model)

    if "private_assumption_data" not in st.session_state:
        st.session_state["private_assumption_data"] = build_assumption_table(document_extraction, financial_model)

    assumption_data = st.session_state["private_assumption_data"]
    counts = assumption_counts(assumption_data)
    readiness = assumption_data.get("readiness_summary", {})

    st.markdown("### 汇总信息")
    summary_cols = st.columns(4)
    summary_cols[0].metric("标的名称", assumption_data.get("target_name") or "未命名项目")
    summary_cols[1].metric("来源文件数量", len(assumption_data.get("source_files", [])))
    summary_cols[2].metric("关键假设总数", counts["total"])
    summary_cols[3].metric("可用于估值计算", counts["usable"])
    confidence_cols = st.columns(5)
    confidence_cols[0].metric("高可信度", counts["high"])
    confidence_cols[1].metric("中可信度", counts["medium"])
    confidence_cols[2].metric("低可信度", counts["low"])
    confidence_cols[3].metric("缺失", counts["missing"])
    confidence_cols[4].metric("需要确认", counts["needs_confirmation"])

    st.markdown("### 估值准备度")
    readiness_cols = st.columns(3)
    readiness_cols[0].metric("准备度等级", readiness.get("valuation_readiness_level", "不足"))
    readiness_cols[1].metric("可进入 V0.6", "是" if readiness.get("ready_for_v0_6_calculation") else "否")
    readiness_cols[2].metric("待补充项", len(readiness.get("missing_before_calculation", [])))
    st.write(readiness.get("reason", "待确认"))

    missing_items = readiness.get("missing_before_calculation", [])
    if missing_items:
        st.markdown("### 缺失关键数据")
        for item in missing_items:
            st.write(f"- {item}缺失")

    st.markdown("### 分组确认")
    for group_key, group_label in ASSUMPTION_GROUP_LABELS.items():
        with st.expander(group_label, expanded=group_key in {"project_basic", "financing_valuation", "revenue"}):
            rows = assumption_data.get("assumption_groups", {}).get(group_key, [])
            edited_rows = st.data_editor(
                rows,
                key=f"assumption_editor_{group_key}",
                use_container_width=True,
                hide_index=True,
                disabled=["field", "extracted_value", "source", "source_file", "source_location", "confidence"],
                column_order=[
                    "field",
                    "extracted_value",
                    "confirmed_value",
                    "unit",
                    "period",
                    "source",
                    "confidence",
                    "needs_confirmation",
                    "use_in_valuation",
                    "notes",
                ],
            )
            if hasattr(edited_rows, "to_dict"):
                edited_rows = edited_rows.to_dict("records")
            assumption_data["assumption_groups"][group_key] = update_group_from_rows(rows, list(edited_rows))

    assumption_data = finalize_assumption_data(assumption_data)
    st.session_state["private_assumption_data"] = assumption_data

    st.markdown("### 保存与输出")
    col_save, col_obsidian = st.columns(2)
    with col_save:
        st.caption(str(PRIVATE_MARKET_CASES_DIR))
        if st.button("保存关键假设确认结果"):
            output_path = save_assumption_confirmation(assumption_data)
            st.session_state["private_assumption_saved_path"] = output_path
            st.success(f"已保存：{output_path}")
            st.code(str(output_path), language="text")
    with col_obsidian:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="assumption_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "关键假设确认"))
        if st.button("生成 Obsidian 关键假设确认报告"):
            try:
                output_path = write_assumption_confirmation_report(assumption_data, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")


def load_assumption_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"读取关键假设 JSON 失败：{exc}")
        return None


def assumption_json_options() -> list[Path]:
    if not PRIVATE_MARKET_CASES_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_CASES_DIR.glob("*_关键假设确认.json"), reverse=True)


def load_basic_valuation_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"读取基础估值计算 JSON 失败：{exc}")
        return None


def load_local_json(path: Path, label: str) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"读取{label} JSON 失败：{exc}")
        return None


def basic_valuation_json_options() -> list[Path]:
    if not PRIVATE_MARKET_CASES_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_CASES_DIR.glob("*_基础估值计算.json"), reverse=True)


def multi_model_json_options() -> list[Path]:
    if not PRIVATE_MARKET_CASES_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_CASES_DIR.glob("*_多模型估值对比.json"), reverse=True)


def investment_memo_json_options() -> list[Path]:
    if not PRIVATE_MARKET_CASES_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_CASES_DIR.glob("*_投资备忘录整合.json"), reverse=True)


def document_extraction_json_options() -> list[Path]:
    if not PRIVATE_MARKET_EXTRACTED_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_EXTRACTED_DIR.glob("*.json"), reverse=True)


def financial_extraction_json_options() -> list[Path]:
    if not PRIVATE_MARKET_FINANCIAL_EXTRACTED_DIR.exists():
        return []
    return sorted(PRIVATE_MARKET_FINANCIAL_EXTRACTED_DIR.glob("*.json"), reverse=True)


def model_results_rows(model_results: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "模型": item.get("model", ""),
            "适用度": item.get("status", ""),
            "输入完整度": item.get("input_completeness", ""),
            "原始估值": item.get("raw_valuation", ""),
            "折扣后估值": item.get("discounted_valuation", ""),
            "置信度": item.get("confidence", ""),
            "主要依据": item.get("主要依据", ""),
            "主要限制": item.get("main_limitations", ""),
        }
        for item in model_results
    ]


def multi_model_comparison_rows(rows: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "模型": item.get("model", ""),
            "适用度": item.get("status", ""),
            "输入完整度": item.get("input_completeness", ""),
            "折扣后估值": item.get("discounted_valuation", ""),
            "置信度": item.get("confidence", ""),
            "主要依据": item.get("basis", ""),
            "主要限制": item.get("limitations", ""),
            "是否可纳入": "是" if item.get("can_include") else "否",
        }
        for item in rows
    ]


def weight_editor_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "模型": item.get("model", ""),
            "默认权重": float(item.get("default_weight", 0)),
            "用户调整权重": float(item.get("user_weight", 0)),
            "是否纳入综合区间": bool(item.get("include_in_range")),
            "权重原因": item.get("weight_reason", ""),
            "模型置信度": item.get("model_confidence", ""),
        }
        for item in rows
    ]


def user_weighting_from_rows(rows) -> list[dict]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    return [
        {
            "model": row.get("模型", ""),
            "user_weight": row.get("用户调整权重", 0),
            "include_in_range": row.get("是否纳入综合区间", False),
        }
        for row in rows
    ]


def weighting_display_rows(rows: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "模型": item.get("model", ""),
            "默认权重": f"{item.get('default_weight', 0):.1f}%",
            "用户调整权重": f"{item.get('user_weight', 0):.1f}%",
            "归一化权重": f"{item.get('normalized_weight', 0):.1%}",
            "是否纳入综合区间": "是" if item.get("include_in_range") else "否",
            "权重原因": item.get("weight_reason", ""),
            "模型置信度": item.get("model_confidence", ""),
        }
        for item in rows
    ]


def model_interval_rows(rows: list[dict]) -> list[dict]:
    chart_rows = []
    for row in rows:
        values = row.get("range_values") or {}
        if not values:
            continue
        chart_rows.append(
            {
                "模型": row.get("model", ""),
                "保守估值": values.get("low"),
                "中性估值": values.get("base"),
                "乐观估值": values.get("high"),
            }
        )
    return chart_rows


def excluded_model_rows(rows: list[dict]) -> list[dict[str, str]]:
    return [{"模型": item.get("model", ""), "原因": item.get("reason", "")} for item in rows]


def memo_section_rows(section: dict) -> list[dict[str, str]]:
    rows = []
    for key, value in section.items():
        if isinstance(value, list):
            display = "、".join(str(item) for item in value) if value else "待补充"
        elif isinstance(value, dict):
            display = json.dumps(value, ensure_ascii=False)
        elif value is None or value == "":
            display = "待补充"
        else:
            display = str(value)
        rows.append({"字段": str(key), "内容": display})
    return rows


def render_memo_section(title: str, section: dict, expanded: bool = False) -> None:
    with st.expander(title, expanded=expanded):
        st.dataframe(memo_section_rows(section), use_container_width=True, hide_index=True)


def due_diligence_question_rows(rows: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "分类": row.get("category", ""),
            "问题": row.get("question", ""),
            "优先级": row.get("priority", ""),
        }
        for row in rows
    ]


def project_card_rows(card: dict) -> list[dict[str, str]]:
    return memo_section_rows(card)


def tracking_task_editor_rows(rows: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "任务": row.get("task", ""),
            "分类": row.get("category", ""),
            "优先级": row.get("priority", "中"),
            "截止日期": row.get("due_date", ""),
            "状态": row.get("status", "todo"),
            "来源": row.get("source", ""),
        }
        for row in rows
    ]


def tracking_tasks_from_editor(rows) -> list[dict]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    return [
        {
            "task": row.get("任务", ""),
            "category": row.get("分类", ""),
            "priority": row.get("优先级", "中"),
            "due_date": row.get("截止日期", ""),
            "status": row.get("状态", "todo"),
            "source": row.get("来源", "用户编辑"),
        }
        for row in rows
        if row.get("任务")
    ]


def load_selected_json(label: str, options: list[Path], key: str) -> dict | None:
    if not options:
        st.caption(f"暂未找到{label} JSON。")
        return st.session_state.get(key)
    selected = st.selectbox(f"选择{label} JSON", options, format_func=lambda path: path.name, key=f"{key}_select")
    if st.button(f"读取{label} JSON", key=f"{key}_button"):
        loaded = load_local_json(selected, label)
        if loaded:
            st.session_state[key] = loaded
    return st.session_state.get(key)


def render_basic_valuation_calculation() -> None:
    st.subheader("基础估值自动计算")
    st.warning("本模块基于用户已确认的关键假设进行基础估值计算。计算结果仅为内部研究参考，不构成投资建议、投资邀约、买卖依据或收益承诺。一级市场估值高度依赖假设质量，请谨慎使用。")

    source_mode = st.radio("关键假设来源", ["使用当前页面已确认假设", "读取已保存关键假设 JSON"], horizontal=True)
    assumption_data = None
    if source_mode == "使用当前页面已确认假设":
        assumption_data = st.session_state.get("private_assumption_data")
        if not assumption_data:
            st.info("当前页面还没有关键假设确认结果，请先在 V0.5 模块生成关键假设表。")
    else:
        options = assumption_json_options()
        if not options:
            st.info(f"暂未找到已保存关键假设 JSON：{PRIVATE_MARKET_CASES_DIR}")
        else:
            selected = st.selectbox("选择关键假设 JSON", options, format_func=lambda path: path.name)
            if st.button("读取关键假设 JSON"):
                assumption_data = load_assumption_json(selected)
                if assumption_data:
                    st.session_state["private_loaded_assumption_data"] = assumption_data
            assumption_data = st.session_state.get("private_loaded_assumption_data")

    if not assumption_data:
        return

    readiness = assumption_data.get("readiness_summary", {})
    st.markdown("### 估值准备度")
    readiness_cols = st.columns(3)
    readiness_cols[0].metric("准备度等级", readiness.get("valuation_readiness_level", "不足"))
    readiness_cols[1].metric("V0.6 可计算", "是" if assumption_data.get("ready_for_valuation_calculation") else "试算")
    readiness_cols[2].metric("待补充项", len(readiness.get("missing_before_calculation", [])))
    st.write(readiness.get("reason", "待确认"))
    if readiness.get("valuation_readiness_level") == "中":
        st.info("部分关键数据仍需确认，结果仅作为初步研究参考。")
    elif readiness.get("valuation_readiness_level") == "低":
        st.warning("低置信度，仅用于理解估值敏感性。")
    elif readiness.get("valuation_readiness_level") == "不足":
        st.error("当前数据不足，不建议进入估值计算。用户仍可手动选择试算。")
        force = st.checkbox("强制试算，并将结果标记为低置信度")
        if not force:
            return

    if st.button("运行基础估值计算"):
        st.session_state["private_basic_valuation_result"] = run_basic_private_market_valuation(assumption_data)

    valuation_result = st.session_state.get("private_basic_valuation_result")
    if not valuation_result:
        return

    st.markdown("### 可计算模型")
    render_list("模型", valuation_result.get("available_models", []))

    st.markdown("### 不可计算模型及缺失字段")
    unavailable_rows = [
        {"模型": item.get("model", ""), "缺失字段": "、".join(item.get("missing_fields", [])), "主要限制": item.get("主要限制", "")}
        for item in valuation_result.get("unavailable_models", [])
    ]
    st.dataframe(unavailable_rows, use_container_width=True, hide_index=True)

    st.markdown("### 模型结果表")
    st.dataframe(model_results_rows(valuation_result.get("model_results", [])), use_container_width=True, hide_index=True)

    st.markdown("### 折扣与风险调整")
    st.dataframe(valuation_result.get("risk_adjustments", []), use_container_width=True, hide_index=True)

    valuation_range = valuation_result.get("valuation_range", {})
    st.markdown("### 初步估值区间")
    range_cols = st.columns(4)
    range_cols[0].metric("保守区间", valuation_range.get("display", "").split(" / ")[0] if valuation_range.get("display") else "不足")
    range_cols[1].metric("中性区间", valuation_range.get("display", "不足"))
    range_cols[2].metric("综合置信度", valuation_result.get("confidence_level", "仅供框架参考"))
    range_cols[3].metric("方法", valuation_range.get("method", ""))
    st.write(valuation_result.get("confidence_reason", ""))

    st.markdown("### 敏感性提示")
    for note in valuation_result.get("sensitivity_notes", []):
        st.write(f"- {note}")

    st.markdown("### 缺失数据提示")
    for item in valuation_result.get("missing_data", []):
        st.write(f"- {item}")

    st.markdown("### 保存与输出")
    col_save, col_obsidian = st.columns(2)
    with col_save:
        st.caption(str(PRIVATE_MARKET_CASES_DIR))
        if st.button("保存基础估值计算 JSON"):
            output_path = save_basic_valuation_result(valuation_result)
            st.success(f"已保存：{output_path}")
            st.code(str(output_path), language="text")
    with col_obsidian:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="basic_valuation_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "基础估值计算"))
        if st.button("生成 Obsidian 基础估值计算报告"):
            try:
                output_path = write_basic_valuation_calculation_report(valuation_result, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")


def render_multi_model_valuation_comparison() -> None:
    st.subheader("多模型估值对比与综合区间")
    st.warning("本模块基于多个估值模型生成综合估值区间。结果仅为内部研究参考，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。模型结果高度依赖已确认关键假设和数据质量。")

    source_mode = st.radio("V0.6 估值结果来源", ["使用当前页面基础估值计算结果", "读取已保存基础估值计算 JSON"], horizontal=True)
    valuation_result = None
    if source_mode == "使用当前页面基础估值计算结果":
        valuation_result = st.session_state.get("private_basic_valuation_result")
        if not valuation_result:
            st.info("当前页面还没有 V0.6 基础估值计算结果，请先运行基础估值自动计算。")
    else:
        options = basic_valuation_json_options()
        if not options:
            st.info(f"暂未找到已保存基础估值计算 JSON：{PRIVATE_MARKET_CASES_DIR}")
        else:
            selected = st.selectbox("选择基础估值计算 JSON", options, format_func=lambda path: path.name)
            if st.button("读取基础估值计算 JSON"):
                valuation_result = load_basic_valuation_json(selected)
                if valuation_result:
                    st.session_state["private_loaded_basic_valuation_result"] = valuation_result
            valuation_result = st.session_state.get("private_loaded_basic_valuation_result")

    if not valuation_result:
        return

    preview_result = run_multi_model_comparison(valuation_result)
    weighted_range = preview_result.get("weighted_valuation_range", {})
    readiness = valuation_result.get("input_summary", {})

    st.markdown("### 估值准备度")
    readiness_cols = st.columns(4)
    readiness_cols[0].metric("标的类型", preview_result.get("target_type", "未确认"))
    readiness_cols[1].metric("V0.5 准备度", readiness.get("valuation_readiness_level", "不足"))
    readiness_cols[2].metric("可纳入模型", weighted_range.get("included_model_count", 0))
    readiness_cols[3].metric("暂不纳入模型", weighted_range.get("excluded_model_count", 0))
    if weighted_range.get("included_model_count", 0) < 2:
        st.warning("可计算模型少于 2 个，仍可查看单模型结果，但综合区间置信度较低。")

    st.markdown("### 可纳入模型列表")
    included_models = [row.get("model", "") for row in preview_result.get("weighting_table", []) if row.get("include_in_range")]
    render_list("模型", included_models)

    st.markdown("### 不可纳入模型列表")
    st.dataframe(excluded_model_rows(preview_result.get("excluded_models", [])), use_container_width=True, hide_index=True)

    st.markdown("### 用户可编辑模型权重表")
    edited_rows = st.data_editor(
        weight_editor_rows(preview_result.get("weighting_table", [])),
        key="multi_model_weight_editor",
        use_container_width=True,
        hide_index=True,
        disabled=["模型", "默认权重", "权重原因", "模型置信度"],
        column_config={
            "用户调整权重": st.column_config.NumberColumn("用户调整权重", min_value=0.0, step=1.0, format="%.1f%%"),
            "是否纳入综合区间": st.column_config.CheckboxColumn("是否纳入综合区间"),
        },
    )
    st.caption("权重总和不等于 100% 时，系统会在纳入模型之间自动归一化。")

    if st.button("生成多模型综合区间"):
        user_weighting = user_weighting_from_rows(edited_rows)
        st.session_state["private_multi_model_valuation_result"] = run_multi_model_comparison(valuation_result, user_weighting)

    multi_model_result = st.session_state.get("private_multi_model_valuation_result")
    if not multi_model_result:
        return

    st.markdown("### 模型结果对比表")
    st.dataframe(multi_model_comparison_rows(multi_model_result.get("model_comparison", [])), use_container_width=True, hide_index=True)

    st.markdown("### 模型权重表")
    st.dataframe(weighting_display_rows(multi_model_result.get("weighting_table", [])), use_container_width=True, hide_index=True)

    st.markdown("### 模型估值结果柱状图")
    interval_rows = model_interval_rows(multi_model_result.get("weighting_table", []))
    base_chart_rows = [{"模型": row["模型"], "base估值": row["中性估值"]} for row in interval_rows]
    if base_chart_rows:
        st.bar_chart(base_chart_rows, x="模型", y="base估值")
    else:
        st.info("暂无可用于图表展示的模型 base 估值。")

    st.markdown("### 模型区间对比图")
    if interval_rows:
        st.bar_chart(interval_rows, x="模型", y=["保守估值", "中性估值", "乐观估值"])

    weighted_range = multi_model_result.get("weighted_valuation_range", {})
    st.markdown("### 加权综合估值区间")
    range_cols = st.columns(5)
    range_cols[0].metric("保守估值", display_money(weighted_range.get("low")))
    range_cols[1].metric("中性估值", display_money(weighted_range.get("base")))
    range_cols[2].metric("乐观估值", display_money(weighted_range.get("high")))
    range_cols[3].metric("纳入模型", weighted_range.get("included_model_count", 0))
    range_cols[4].metric("剔除模型", weighted_range.get("excluded_model_count", 0))
    st.write(weighted_range.get("weight_source", ""))

    dispersion = multi_model_result.get("model_dispersion", {})
    st.markdown("### 模型分歧度")
    dispersion_cols = st.columns(4)
    dispersion_cols[0].metric("最低模型估值", display_money(dispersion.get("min_value")))
    dispersion_cols[1].metric("最高模型估值", display_money(dispersion.get("max_value")))
    spread_ratio = dispersion.get("spread_ratio")
    dispersion_cols[2].metric("分歧倍数", f"{spread_ratio:.2f}x" if spread_ratio else "无法判断")
    dispersion_cols[3].metric("分歧等级", dispersion.get("dispersion_level", "无法判断"))
    st.write(dispersion.get("reason", ""))

    st.markdown("### 综合置信度")
    st.metric("综合置信度", multi_model_result.get("confidence_level", "仅供框架参考"))
    st.write(multi_model_result.get("confidence_reason", ""))

    st.markdown("### 主要分歧来源")
    for item in multi_model_result.get("major_divergence_drivers", []):
        st.write(f"- {item}")

    st.markdown("### 敏感性提示")
    for note in multi_model_result.get("sensitivity_notes", []):
        st.write(f"- {note}")

    st.markdown("### 被剔除模型说明")
    st.dataframe(excluded_model_rows(multi_model_result.get("excluded_models", [])), use_container_width=True, hide_index=True)

    st.markdown("### 保存与输出")
    col_save, col_obsidian = st.columns(2)
    with col_save:
        st.caption(str(PRIVATE_MARKET_CASES_DIR))
        if st.button("保存多模型估值 JSON"):
            output_path = save_multi_model_valuation_result(multi_model_result)
            st.success(f"已保存：{output_path}")
            st.code(str(output_path), language="text")
    with col_obsidian:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="multi_model_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "15_估值引擎" / "多模型估值对比"))
        if st.button("生成 Obsidian 多模型估值对比报告"):
            try:
                output_path = write_multi_model_valuation_report(multi_model_result, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")


def render_investment_memo_builder() -> None:
    st.subheader("投资备忘录 / 尽调问题 / 研究动作建议")
    st.warning("本模块生成的是内部投资备忘录草稿与尽调问题清单，仅用于 Rachel Capital OS 内部研究，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。所有结论均需人工复核。")

    source_mode = st.radio("V0.8 输入来源", ["优先使用当前页面数据", "读取本地 JSON 数据"], horizontal=True)
    if source_mode == "优先使用当前页面数据":
        document_extraction = st.session_state.get("private_document_extraction")
        financial_extraction = st.session_state.get("private_financial_model")
        assumption_confirmation = st.session_state.get("private_assumption_data")
        basic_valuation_result = st.session_state.get("private_basic_valuation_result")
        multi_model_result = st.session_state.get("private_multi_model_valuation_result")
        st.caption("将优先读取当前页面 session_state 中已经完成的项目资料、财务模型、关键假设、基础估值和多模型估值结果。")
    else:
        with st.expander("读取本地 JSON 数据", expanded=True):
            document_extraction = load_selected_json("项目资料解析", document_extraction_json_options(), "private_loaded_document_extraction_for_memo")
            financial_extraction = load_selected_json("财务模型解析", financial_extraction_json_options(), "private_loaded_financial_extraction_for_memo")
            assumption_confirmation = load_selected_json("关键假设确认", assumption_json_options(), "private_loaded_assumption_for_memo")
            basic_valuation_result = load_selected_json("基础估值计算", basic_valuation_json_options(), "private_loaded_basic_valuation_for_memo")
            multi_model_result = load_selected_json("多模型估值对比", multi_model_json_options(), "private_loaded_multi_model_for_memo")

    preview_memo = build_private_market_investment_memo(
        document_extraction,
        financial_extraction,
        assumption_confirmation,
        basic_valuation_result,
        multi_model_result,
    )

    st.markdown("### 输入数据读取状态")
    input_status = preview_memo.get("input_status", {})
    status_cols = st.columns(4)
    status_cols[0].metric("Memo 完整度", preview_memo.get("memo_completeness", "不足"))
    status_cols[1].metric("已读取模块", len(input_status.get("loaded_modules", [])))
    status_cols[2].metric("缺失模块", len(input_status.get("missing_modules", [])))
    status_cols[3].metric("数据缺口", len(preview_memo.get("data_gaps", [])))
    st.write(preview_memo.get("memo_completeness_reason", ""))
    st.caption(input_status.get("quality_impact", ""))

    status_rows = [
        {"模块": label, "状态": "已读取" if input_status.get("modules", {}).get(key) else "缺失"}
        for key, label in {
            "document_extraction": "项目资料解析",
            "financial_extraction": "财务模型解析",
            "assumption_confirmation": "关键假设确认",
            "basic_valuation_result": "基础估值计算",
            "multi_model_result": "多模型估值对比",
        }.items()
    ]
    st.dataframe(status_rows, use_container_width=True, hide_index=True)

    if st.button("生成投资备忘录草稿"):
        st.session_state["private_investment_memo_result"] = preview_memo

    memo_data = st.session_state.get("private_investment_memo_result")
    if not memo_data:
        return

    render_memo_section("项目快照", memo_data.get("project_snapshot", {}), expanded=True)
    render_memo_section("创始团队评估", memo_data.get("founder_team_review", {}))
    render_memo_section("商业模式评估", memo_data.get("business_model_review", {}))
    render_memo_section("技术与壁垒评估", memo_data.get("technology_review", {}))
    render_memo_section("产品与客户评估", memo_data.get("product_customer_review", {}))
    render_memo_section("市场与竞争评估", memo_data.get("market_competition_review", {}))
    render_memo_section("财务与经营评估", memo_data.get("financial_review", {}), expanded=True)
    render_memo_section("融资与估值评估", memo_data.get("financing_valuation_review", {}), expanded=True)
    render_memo_section("主要风险", memo_data.get("risk_summary", {}), expanded=True)

    with st.expander("尽调问题清单", expanded=True):
        st.dataframe(due_diligence_question_rows(memo_data.get("due_diligence_questions", [])), use_container_width=True, hide_index=True)

    with st.expander("数据缺口", expanded=True):
        render_list("缺口清单", memo_data.get("data_gaps", []))

    st.markdown("### 研究动作建议")
    research_action = memo_data.get("research_action", {})
    action_cols = st.columns(2)
    action_cols[0].metric("建议动作", research_action.get("suggested_action", "需要补充数据"))
    action_cols[1].metric("下次复查", memo_data.get("for_v0_9_project_tracking", {}).get("next_review_date", "待确认"))
    st.write(research_action.get("reason", ""))
    render_list("后续研究任务", research_action.get("next_steps", []))

    st.markdown("### 保存与输出")
    col_save, col_memo, col_questions = st.columns(3)
    with col_save:
        st.caption(str(PRIVATE_MARKET_CASES_DIR))
        if st.button("保存 V0.8 投资备忘录整合 JSON"):
            output_path = save_investment_memo_result(memo_data)
            st.success(f"已保存：{output_path}")
            st.code(str(output_path), language="text")
    with col_memo:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="investment_memo_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "16_投资决策引擎" / "投资备忘录"))
        if st.button("生成 Obsidian 投资备忘录草稿"):
            try:
                output_path = write_private_market_investment_memo(memo_data, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")
    with col_questions:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="due_diligence_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "16_投资决策引擎" / "尽调问题清单"))
        if st.button("生成 Obsidian 尽调问题清单"):
            try:
                output_path = write_due_diligence_questions(memo_data, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")


def render_project_tracking_watchlist() -> None:
    st.subheader("项目观察池 / 跟踪任务 / 项目卡片")
    st.warning("本模块用于将项目纳入 Rachel Capital OS 内部观察池并生成后续跟踪任务，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。项目状态和研究动作均需人工复核。")

    source_mode = st.radio("V0.9 输入来源", ["使用当前 V0.8 投资备忘录", "读取本地投资备忘录 JSON", "手动填写观察池信息"], horizontal=True)
    memo_data = None
    if source_mode == "使用当前 V0.8 投资备忘录":
        memo_data = st.session_state.get("private_investment_memo_result")
        if not memo_data:
            st.info("当前页面还没有 V0.8 投资备忘录整合结果，可以先生成 Memo，或切换为读取本地 JSON / 手动填写。")
    elif source_mode == "读取本地投资备忘录 JSON":
        with st.expander("读取 V0.8 投资备忘录整合 JSON", expanded=True):
            memo_data = load_selected_json("投资备忘录整合", investment_memo_json_options(), "private_loaded_investment_memo_for_tracking")
    else:
        st.info("未读取 V0.8 结果时，可以手动建立观察池记录；系统会将完整度和来源风险标记为较低。")

    preview_record = build_project_tracking_record(memo_data, {})
    source_status = "已读取 V0.8 Memo" if memo_data else "未读取 V0.8 Memo / 手动模式"
    st.markdown("### 输入数据读取状态")
    status_cols = st.columns(4)
    status_cols[0].metric("输入状态", source_status)
    status_cols[1].metric("研究动作", preview_record.get("research_action", ""))
    status_cols[2].metric("系统项目状态", preview_record.get("project_status", ""))
    status_cols[3].metric("系统观察池状态", preview_record.get("watchlist_status_label", ""))

    if preview_record.get("research_action") == "暂不进入估值":
        st.warning("V0.8 研究动作建议为“暂不进入估值”，默认不进入活跃观察池；如需纳入，请在下方手动覆盖状态。")

    st.markdown("### 状态与复查日期")
    manual_cols = st.columns(4)
    default_target = preview_record.get("target_name", "未命名项目")
    target_name = manual_cols[0].text_input("项目名称", value=default_target, key="tracking_target_name")
    project_status = manual_cols[1].selectbox(
        "项目状态",
        PROJECT_STATUS_OPTIONS,
        index=PROJECT_STATUS_OPTIONS.index(preview_record.get("project_status")) if preview_record.get("project_status") in PROJECT_STATUS_OPTIONS else 0,
        key="tracking_project_status",
    )
    watchlist_status = manual_cols[2].selectbox(
        "观察池状态",
        WATCHLIST_STATUS_OPTIONS,
        format_func=lambda value: f"{WATCHLIST_STATUS_LABELS.get(value, value)} ({value})",
        index=WATCHLIST_STATUS_OPTIONS.index(preview_record.get("watchlist_status")) if preview_record.get("watchlist_status") in WATCHLIST_STATUS_OPTIONS else 0,
        key="tracking_watchlist_status",
    )
    suggested_review = preview_record.get("next_review_date") or suggest_next_review_date(watchlist_status, project_status)
    next_review_date = manual_cols[3].text_input("下次复查日期", value=suggested_review, key="tracking_next_review_date")

    st.caption(f"系统建议下次复查日期：{suggested_review or '暂不设置'}。用户可以手动修改。")

    preview_manual = {
        "target_name": target_name,
        "project_status": project_status,
        "watchlist_status": watchlist_status,
        "next_review_date": next_review_date,
    }
    preview_record = build_project_tracking_record(memo_data, preview_manual)

    st.markdown("### 项目卡片预览")
    with st.expander("项目卡片", expanded=True):
        st.dataframe(project_card_rows(preview_record.get("project_card", {})), use_container_width=True, hide_index=True)

    col_gap, col_question, col_risk = st.columns(3)
    with col_gap:
        render_list("数据缺口", preview_record.get("data_gaps", []))
    with col_question:
        render_list("需要向项目方追问的问题", preview_record.get("questions_for_company", [])[:12])
    with col_risk:
        render_list("风险标记", preview_record.get("risk_flags", []))

    st.markdown("### 跟踪任务列表")
    edited_tasks = st.data_editor(
        tracking_task_editor_rows(preview_record.get("tracking_tasks", [])),
        key="tracking_task_editor",
        use_container_width=True,
        hide_index=True,
        column_config={
            "优先级": st.column_config.SelectboxColumn("优先级", options=["高", "中", "低"]),
            "状态": st.column_config.SelectboxColumn("状态", options=["todo", "doing", "done", "blocked"]),
        },
    )

    if st.button("生成 / 刷新项目跟踪记录"):
        manual_inputs = {
            **preview_manual,
            "tracking_tasks": tracking_tasks_from_editor(edited_tasks),
        }
        st.session_state["private_project_tracking_record"] = build_project_tracking_record(memo_data, manual_inputs)

    tracking_record = st.session_state.get("private_project_tracking_record")
    if not tracking_record:
        return

    st.markdown("### 项目跟踪记录")
    record_cols = st.columns(5)
    record_cols[0].metric("项目状态", tracking_record.get("project_status", ""))
    record_cols[1].metric("观察池状态", tracking_record.get("watchlist_status_label", ""))
    record_cols[2].metric("研究动作", tracking_record.get("research_action", ""))
    record_cols[3].metric("下次复查日期", tracking_record.get("next_review_date", "") or "暂不设置")
    record_cols[4].metric("跟踪任务", len(tracking_record.get("tracking_tasks", [])))

    with st.expander("V1.0 投委会工作流预留接口", expanded=False):
        st.json(tracking_record.get("for_v1_0_portfolio_decision", {}))

    st.markdown("### 保存与输出")
    col_save, col_card, col_tasks, col_watchlist = st.columns(4)
    with col_save:
        st.caption(str(PRIVATE_MARKET_CASES_DIR))
        if st.button("保存 V0.9 项目跟踪 JSON"):
            output_path = save_project_tracking_result(tracking_record)
            st.success(f"已保存：{output_path}")
            st.code(str(output_path), language="text")
    with col_card:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="project_card_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "03_公司数据库" / "一级市场项目"))
        if st.button("生成 Obsidian 项目卡片"):
            try:
                output_path = write_private_market_project_card(tracking_record, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")
    with col_tasks:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="tracking_tasks_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "16_投资决策引擎" / "项目跟踪任务"))
        if st.button("生成 Obsidian 项目跟踪任务"):
            try:
                output_path = write_project_tracking_tasks(tracking_record, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成：{output_path}")
                st.code(str(output_path), language="text")
    with col_watchlist:
        vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path(), key="watchlist_vault_path")
        st.caption(str(Path(vault_path).expanduser() / "03_公司数据库" / "一级市场项目" / "一级市场项目观察池.md"))
        if st.button("生成 / 更新项目观察池总览"):
            try:
                output_path = update_private_market_project_watchlist(tracking_record, vault_path)
            except OSError as exc:
                st.error(f"生成失败：{exc}")
            else:
                st.success(f"已生成或更新：{output_path}")
                st.code(str(output_path), language="text")


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
        apply_private_market_autofill(build_private_market_autofill_from_document(extraction), "项目资料")

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
                output_path = write_private_market_document_valuation_framework(
                    extraction,
                    parsed_document,
                    vault_path,
                    st.session_state.get("private_financial_model"),
                )
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
    ensure_private_form_defaults()
    st.header("未上市 / 一级市场估值")
    st.caption("用于未上市成长公司、融资交易、Pre-IPO、老股转让、项目公司 / SPV、资产型项目。")
    render_private_document_upload()
    st.divider()
    render_financial_model_upload()
    st.divider()
    render_assumption_confirmation_page()
    st.divider()
    render_basic_valuation_calculation()
    st.divider()
    render_multi_model_valuation_comparison()
    st.divider()
    render_investment_memo_builder()
    st.divider()
    render_project_tracking_watchlist()
    st.divider()
    render_private_autofill_message()
    st.subheader("标的基本信息")
    col_1, col_2, col_3 = st.columns(3)
    target_name = col_1.text_input("标的名称", placeholder="例如：OpenAI 老股交易 / 信宜绿色算力中心", key="private_target_name")
    initial_type = col_2.selectbox("标的类型初选", PRIVATE_TARGET_TYPES, key="private_initial_type")
    private_industry = col_3.text_input("所属行业", placeholder="例如：AI应用 / 绿色算力 / 资源回收", key="private_industry")
    private_ecosystem = st.selectbox("所属 Rachel 战略生态", ECOSYSTEM_OPTIONS, key="private_ecosystem")

    st.subheader("交易 / 项目特征")
    col_a, col_b, col_c, col_d = st.columns(4)
    is_financing_or_transfer = col_a.checkbox("是否正在融资或老股转让", key="private_is_financing_or_transfer")
    is_complete_company = col_b.checkbox("是否为完整公司主体", key="private_is_complete_company")
    is_single_project_spv = col_c.checkbox("是否为单一项目 / SPV", key="private_is_single_project_spv")
    is_asset_or_contract_based = col_d.checkbox("是否主要依赖资产、资源、牌照或合同", key="private_is_asset_or_contract_based")

    col_e, col_f, col_g, col_h = st.columns(4)
    has_revenue = col_e.checkbox("是否已有收入", key="private_has_revenue")
    is_private_profitable = col_f.checkbox("是否盈利", key="private_is_profitable")
    private_revenue_growth = col_g.selectbox("收入增长状态", PRIVATE_REVENUE_GROWTH, key="private_revenue_growth")
    private_cash_flow_stable = col_h.checkbox("现金流是否稳定", key="private_cash_flow_stable")
    exit_path = st.selectbox("退出路径", EXIT_PATHS, key="private_exit_path")

    financing_round = pre_money = post_money = financing_amount = equity_sold = previous_round_valuation = previous_round_date = None
    if initial_type == "一级市场融资标的" or is_financing_or_transfer:
        st.subheader("一级市场专用字段")
        col_i, col_j, col_k, col_l = st.columns(4)
        financing_round = col_i.selectbox("本轮融资类型", FINANCING_ROUNDS, key="private_financing_round")
        pre_money = col_j.text_input("投前估值", key="private_pre_money")
        post_money = col_k.text_input("投后估值", key="private_post_money")
        financing_amount = col_l.text_input("本轮融资金额", key="private_financing_amount")
        col_m, col_n, col_o = st.columns(3)
        equity_sold = col_m.text_input("出让股权比例", key="private_equity_sold")
        previous_round_valuation = col_n.text_input("上一轮估值", key="private_previous_round_valuation")
        previous_round_date = col_o.text_input("上一轮融资时间", key="private_previous_round_date")

    project_total_investment = construction_period = expected_revenue = expected_gross_margin = expected_net_margin = annual_cash_flow = payback_period = government_subsidy = utilization_rate = None
    key_contract_signed = None
    if initial_type == "项目公司 / SPV" or is_single_project_spv:
        st.subheader("项目公司 / SPV 专用字段")
        col_p, col_q, col_r, col_s = st.columns(4)
        project_total_investment = col_p.text_input("项目总投资", key="private_project_total_investment")
        construction_period = col_q.text_input("建设周期", key="private_construction_period")
        expected_revenue = col_r.text_input("预计收入", key="private_expected_revenue")
        expected_gross_margin = col_s.text_input("预计毛利率", key="private_expected_gross_margin")
        col_t, col_u, col_v, col_w = st.columns(4)
        expected_net_margin = col_t.text_input("预计净利率", key="private_expected_net_margin")
        annual_cash_flow = col_u.text_input("年现金流", key="private_annual_cash_flow")
        payback_period = col_v.text_input("回收期", key="private_payback_period")
        government_subsidy = col_w.text_input("政府补贴", key="private_government_subsidy")
        col_x, col_y = st.columns(2)
        key_contract_signed = col_x.checkbox("关键合同是否已签署", key="private_key_contract_signed")
        utilization_rate = col_y.text_input("产能利用率 / 上架率 / 负荷率", key="private_utilization_rate")

    asset_type = book_value = replacement_cost = comparable_transaction_price = None
    asset_generates_cash_flow = asset_is_scarce = asset_is_tradeable = asset_has_long_contract = asset_has_policy_restriction = None
    if initial_type == "资产型项目" or is_asset_or_contract_based:
        st.subheader("资产型项目专用字段")
        col_z, col_aa, col_ab, col_ac = st.columns(4)
        asset_type = col_z.text_input("资产类型", key="private_asset_type")
        book_value = col_aa.text_input("资产账面价值", key="private_book_value")
        replacement_cost = col_ab.text_input("重置成本", key="private_replacement_cost")
        comparable_transaction_price = col_ac.text_input("可比交易价格", key="private_comparable_transaction_price")
        col_ad, col_ae, col_af, col_ag, col_ah = st.columns(5)
        asset_generates_cash_flow = col_ad.checkbox("是否产生现金流", key="private_asset_generates_cash_flow")
        asset_is_scarce = col_ae.checkbox("是否具备稀缺性", key="private_asset_is_scarce")
        asset_is_tradeable = col_af.checkbox("是否可交易", key="private_asset_is_tradeable")
        asset_has_long_contract = col_ag.checkbox("是否有长期合同", key="private_asset_has_long_contract")
        asset_has_policy_restriction = col_ah.checkbox("是否有政策限制", key="private_asset_has_policy_restriction")

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
