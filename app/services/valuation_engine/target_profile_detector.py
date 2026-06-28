from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS, EXIT_PATHS, PRIVATE_REVENUE_GROWTH, PRIVATE_TARGET_TYPES


PROFILE_FIELDS = [
    "target_name",
    "target_type",
    "industry",
    "rachel_ecosystem",
    "is_financing_or_secondary_transfer",
    "is_complete_company",
    "is_single_project_spv",
    "is_asset_based",
    "has_revenue",
    "is_profitable",
    "revenue_growth_status",
    "cash_flow_stability",
    "exit_path",
]


def build_target_profile(
    document_extraction: dict[str, Any] | None = None,
    financial_extraction: dict[str, Any] | None = None,
    assumption_confirmation: dict[str, Any] | None = None,
    memo_data: dict[str, Any] | None = None,
    tracking_record: dict[str, Any] | None = None,
    manual_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document_extraction = normalize_document_extraction(document_extraction)
    financial_extraction = financial_extraction or {}
    assumption_confirmation = assumption_confirmation or {}
    memo_data = memo_data or {}
    tracking_record = tracking_record or {}
    manual_inputs = manual_inputs or {}

    text = searchable_text(document_extraction, financial_extraction, assumption_confirmation, memo_data, tracking_record)
    field_map = {
        "target_name": detect_target_name(document_extraction, financial_extraction, assumption_confirmation, memo_data, tracking_record, manual_inputs),
        "target_type": detect_target_type(text, document_extraction, financial_extraction, assumption_confirmation, memo_data, tracking_record, manual_inputs),
        "industry": detect_industry(text, document_extraction, memo_data, tracking_record, assumption_confirmation, manual_inputs),
        "rachel_ecosystem": empty_field(),
        "is_financing_or_secondary_transfer": detect_boolean(
            text,
            [
                "本轮融资",
                "融资金额",
                "投前估值",
                "投后估值",
                "financing_amount",
                "pre_money_valuation",
                "post_money_valuation",
                "equity_offered",
                "老股转让",
                "出让股权",
                "出让比例",
                "Pre-A",
                "A轮",
                "B轮",
                "C轮",
            ],
            "系统推断",
            manual_inputs.get("is_financing_or_secondary_transfer"),
        ),
        "is_complete_company": detect_complete_company(text, document_extraction, memo_data, manual_inputs),
        "is_single_project_spv": detect_boolean(
            text,
            ["单一项目", "SPV", "项目公司", "项目总投资", "建设期", "建设周期", "投资回收期", "项目IRR", "项目 IRR", "项目现金流"],
            "系统推断",
            manual_inputs.get("is_single_project_spv"),
        ),
        "is_asset_based": detect_boolean(
            text,
            ["资产", "资源", "牌照", "土地", "机柜", "矿权", "电力指标", "合同", "产能", "固定资产", "重置成本", "资产包"],
            "系统推断",
            manual_inputs.get("is_asset_based"),
        ),
        "has_revenue": detect_has_revenue(text, document_extraction, financial_extraction, assumption_confirmation, manual_inputs),
        "is_profitable": detect_is_profitable(text, document_extraction, financial_extraction, assumption_confirmation, manual_inputs),
        "revenue_growth_status": detect_revenue_growth(text, document_extraction, financial_extraction, assumption_confirmation, manual_inputs),
        "cash_flow_stability": detect_cash_flow_stability(text, document_extraction, financial_extraction, assumption_confirmation, manual_inputs),
        "exit_path": detect_exit_path(text, document_extraction, assumption_confirmation, memo_data, manual_inputs),
    }
    field_map["rachel_ecosystem"] = detect_ecosystem(field_map["industry"]["confirmed_value"], text, document_extraction, memo_data, manual_inputs)
    target_type = field_map["target_type"]["confirmed_value"]
    field_map["classification_reason"] = classification_reason(target_type, text)
    field_map["warnings"] = build_warnings(field_map)
    return field_map


def detect_target_name(
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any],
    memo_data: dict[str, Any],
    tracking_record: dict[str, Any],
    manual_inputs: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        (memo_data.get("target_name"), "V0.8 Memo", "高"),
        (tracking_record.get("target_name"), "V0.9 项目跟踪记录", "高"),
        (assumption_confirmation.get("target_name"), "关键假设确认", "高"),
        (document_extraction.get("project_basic_info", {}).get("project_name"), "项目资料解析", "高"),
        (document_extraction.get("project_basic_info", {}).get("company_name"), "项目资料解析", "中"),
        (filename_project_name(document_extraction.get("_source_file") or financial_extraction.get("file_name")), "文件名", "低"),
        (manual_inputs.get("target_name"), "用户手动输入", "中"),
    ]
    return first_field(candidates, manual_inputs.get("target_name"))


def detect_target_type(
    text: str,
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any],
    memo_data: dict[str, Any],
    tracking_record: dict[str, Any],
    manual_inputs: dict[str, Any],
) -> dict[str, Any]:
    direct = first_value(
        manual_inputs.get("target_type"),
        tracking_record.get("project_card", {}).get("target_type"),
        memo_data.get("project_snapshot", {}).get("标的类型"),
        memo_data.get("target_type"),
        assumption_value(assumption_confirmation, "project_basic", "标的类型"),
        document_extraction.get("project_basic_info", {}).get("target_type_guess"),
    )
    if direct and direct != "不确定，让系统判断":
        return field(normalize_option(direct, PRIVATE_TARGET_TYPES, "未上市成长公司"), "系统识别 / 用户确认", "中", confirmed=manual_inputs.get("target_type"))
    spv_score = keyword_count(text, ["单一项目", "SPV", "项目公司", "项目总投资", "建设周期", "产能爬坡", "IRR", "投资回收期", "项目现金流"])
    asset_score = keyword_count(text, ["土地", "矿权", "牌照", "电力指标", "机柜", "固定资产", "重置成本", "资产包", "产能", "资源"])
    financing_score = keyword_count(
        text,
        [
            "融资轮次",
            "本轮融资",
            "投前估值",
            "投后估值",
            "出让股权",
            "融资金额",
            "financing_amount",
            "pre_money_valuation",
            "post_money_valuation",
            "equity_offered",
            "公司主体",
            "产品",
            "客户",
            "收入",
        ],
    )
    if spv_score >= 2:
        value, confidence = "项目公司 / SPV", "高" if spv_score >= 4 else "中"
    elif asset_score >= 2:
        value, confidence = "资产型项目", "高" if asset_score >= 4 else "中"
    elif financing_score >= 2:
        value, confidence = "一级市场融资标的", "高" if financing_score >= 4 else "中"
    else:
        value, confidence = "未上市成长公司", "低"
    return field(value, "系统推断", confidence, confirmed=manual_inputs.get("target_type"), notes="根据融资、项目、资产和经营关键词判断。")


def detect_industry(
    text: str,
    document_extraction: dict[str, Any],
    memo_data: dict[str, Any],
    tracking_record: dict[str, Any],
    assumption_confirmation: dict[str, Any],
    manual_inputs: dict[str, Any],
) -> dict[str, Any]:
    direct = first_value(
        manual_inputs.get("industry"),
        tracking_record.get("project_card", {}).get("industry"),
        memo_data.get("project_snapshot", {}).get("所属行业"),
        assumption_value(assumption_confirmation, "project_basic", "所属行业"),
        document_extraction.get("project_basic_info", {}).get("industry"),
    )
    if direct:
        return field(direct, "项目资料 / Memo", "中", confirmed=manual_inputs.get("industry"))
    mappings = [
        ("AI应用 / SaaS / 大模型", ["AI应用", "大模型", "Agent", "软件", "SaaS"]),
        ("AI基础设施 / 算力 / 数据中心", ["算力", "数据中心", "IDC", "GPU", "服务器"]),
        ("半导体 / 芯片 / 设备 / 材料", ["半导体", "芯片", "设备", "材料"]),
        ("机器人 / 自动化 / 传感器", ["机器人", "自动化", "传感器"]),
        ("高端材料 / 新材料 / 资源回收", ["新材料", "化工", "资源回收", "氟化钙", "石墨"]),
        ("新能源 / 储能 / 光伏 / 电池", ["新能源", "储能", "光伏", "电池"]),
        ("医疗科技 / 医疗器械 / 生物科技", ["医疗科技", "医疗器械", "生物科技", "AI医疗"]),
        ("船舶与国防 / 航空航天 / 军工", ["船舶", "国防", "航空航天", "军工"]),
    ]
    for industry, keywords in mappings:
        if any(keyword in text for keyword in keywords):
            return field(industry, "系统推断", "中", confirmed=manual_inputs.get("industry"))
    return field("", "缺失", "缺失", confirmed=manual_inputs.get("industry"), needs_confirmation=True)


def detect_ecosystem(industry: str, text: str, document_extraction: dict[str, Any], memo_data: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    direct = first_value(
        manual_inputs.get("rachel_ecosystem"),
        memo_data.get("project_snapshot", {}).get("所属 Rachel 战略生态"),
        document_extraction.get("project_basic_info", {}).get("rachel_ecosystem_guess"),
    )
    if direct:
        return field(normalize_option(direct, ECOSYSTEM_OPTIONS, "其他"), "项目资料 / Memo", "中", confirmed=manual_inputs.get("rachel_ecosystem"))
    combined = f"{industry} {text}"
    mapping = [
        ("华为生态", ["华为", "鸿蒙", "昇腾", "鲲鹏"]),
        ("AI基础设施生态", ["算力", "数据中心", "IDC", "GPU", "服务器", "AI应用", "SaaS", "大模型", "Agent"]),
        ("半导体生态", ["半导体", "芯片", "设备", "材料"]),
        ("机器人生态", ["机器人", "自动化", "传感器"]),
        ("高端材料生态", ["新材料", "化工", "资源回收", "氟化钙", "石墨"]),
        ("船舶与国防生态", ["船舶", "国防", "航空航天", "军工"]),
        ("医疗科技生态", ["医疗器械", "生物科技", "AI医疗"]),
    ]
    for ecosystem, keywords in mapping:
        if ecosystem in ECOSYSTEM_OPTIONS and any(keyword in combined for keyword in keywords):
            return field(ecosystem, "系统推断", "中", confirmed=manual_inputs.get("rachel_ecosystem"))
    return field("其他", "系统推断", "低", confirmed=manual_inputs.get("rachel_ecosystem"), needs_confirmation=True)


def detect_complete_company(text: str, document_extraction: dict[str, Any], memo_data: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    if manual_inputs.get("is_complete_company") is not None:
        return field(bool(manual_inputs["is_complete_company"]), "用户手动输入", "中")
    if keyword_count(text, ["单一项目", "SPV", "项目公司", "项目总投资"]) >= 2:
        return field(False, "系统推断", "中", needs_confirmation=True)
    if keyword_count(text, ["公司名称", "主营业务", "团队", "股权结构", "多产品", "多客户", "历史财务", "融资历史"]) >= 2:
        return field(True, "系统推断", "中")
    if document_extraction.get("project_basic_info", {}).get("company_name") or memo_data.get("project_snapshot", {}).get("公司名称"):
        return field(True, "系统推断", "中")
    return field(True, "系统默认", "低", needs_confirmation=True)


def detect_has_revenue(text: str, document_extraction: dict[str, Any], financial_extraction: dict[str, Any], assumption_confirmation: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    if manual_inputs.get("has_revenue") is not None:
        return field(bool(manual_inputs["has_revenue"]), "用户手动输入", "中")
    revenue_values = [
        document_extraction.get("financial_data", {}).get("historical_revenue"),
        document_extraction.get("financial_data", {}).get("forecast_revenue"),
        financial_field(financial_extraction, "历史收入"),
        financial_field(financial_extraction, "预测收入"),
        assumption_value(assumption_confirmation, "revenue", "历史收入"),
        assumption_value(assumption_confirmation, "revenue", "预测收入"),
    ]
    if any(is_positive_number(value) for value in revenue_values) or any(has_value(value) for value in revenue_values):
        return field(True, "BP / Excel 明确披露", "高")
    if "收入" in text:
        return field(True, "系统推断", "中", needs_confirmation=True)
    return field(False, "缺失", "低", needs_confirmation=True)


def detect_is_profitable(text: str, document_extraction: dict[str, Any], financial_extraction: dict[str, Any], assumption_confirmation: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    if manual_inputs.get("is_profitable") is not None:
        return field(bool(manual_inputs["is_profitable"]), "用户手动输入", "中")
    values = [
        document_extraction.get("financial_data", {}).get("net_margin"),
        document_extraction.get("financial_data", {}).get("ebitda"),
        financial_field(financial_extraction, "净利润"),
        financial_field(financial_extraction, "净利率"),
        financial_field(financial_extraction, "EBITDA"),
        assumption_value(assumption_confirmation, "cost_profit", "净利润"),
        assumption_value(assumption_confirmation, "cost_profit", "净利率"),
        assumption_value(assumption_confirmation, "cost_profit", "EBITDA"),
    ]
    if any(is_positive_number(value) for value in values) or any(has_value(value) and "亏损" not in str(value) for value in values):
        return field(True, "BP / Excel 明确披露", "中")
    if "亏损" in text:
        return field(False, "系统推断", "中")
    return field(False, "缺失", "低", needs_confirmation=True)


def detect_revenue_growth(text: str, document_extraction: dict[str, Any], financial_extraction: dict[str, Any], assumption_confirmation: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    if manual_inputs.get("revenue_growth_status"):
        return field(normalize_option(manual_inputs["revenue_growth_status"], PRIVATE_REVENUE_GROWTH, PRIVATE_REVENUE_GROWTH[0]), "用户手动输入", "中")
    growth = first_value(financial_field(financial_extraction, "收入增长率"), assumption_value(assumption_confirmation, "revenue", "收入增长率"))
    number = parse_percent(growth)
    if number is not None:
        if number > 0.3:
            value = "高增长"
        elif number >= 0.1:
            value = "稳定增长"
        elif number >= 0:
            value = "稳定增长"
        else:
            value = "周期波动"
        return field(value, "Excel明确披露", "高")
    if has_value(document_extraction.get("financial_data", {}).get("forecast_revenue")):
        return field("高增长", "系统推断", "中", needs_confirmation=True)
    if has_value(document_extraction.get("financial_data", {}).get("historical_revenue")):
        return field("稳定增长", "系统推断", "中", needs_confirmation=True)
    return field(PRIVATE_REVENUE_GROWTH[0], "缺失", "低", needs_confirmation=True)


def detect_cash_flow_stability(text: str, document_extraction: dict[str, Any], financial_extraction: dict[str, Any], assumption_confirmation: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    if manual_inputs.get("cash_flow_stability") is not None:
        return field(bool(manual_inputs["cash_flow_stability"]), "用户手动输入", "中")
    values = [
        document_extraction.get("financial_data", {}).get("cash_flow"),
        financial_field(financial_extraction, "项目现金流"),
        financial_field(financial_extraction, "经营现金流"),
        financial_field(financial_extraction, "自由现金流"),
        assumption_value(assumption_confirmation, "cash_flow", "项目现金流"),
        assumption_value(assumption_confirmation, "cash_flow", "经营现金流"),
        assumption_value(assumption_confirmation, "cash_flow", "自由现金流"),
    ]
    if any(has_value(value) for value in values):
        return field(True, "BP / Excel 明确披露", "中", needs_confirmation=True, notes="已识别现金流字段，稳定性仍需核验连续期间。")
    return field(False, "缺失", "低", needs_confirmation=True)


def detect_exit_path(text: str, document_extraction: dict[str, Any], assumption_confirmation: dict[str, Any], memo_data: dict[str, Any], manual_inputs: dict[str, Any]) -> dict[str, Any]:
    direct = first_value(manual_inputs.get("exit_path"), assumption_value(assumption_confirmation, "financing_valuation", "退出路径"))
    if direct:
        return field(normalize_exit_path(direct), "用户确认 / 关键假设", "中", confirmed=manual_inputs.get("exit_path"))
    exit_data = document_extraction.get("exit_path", {})
    for key, option in [("ipo", "IPO"), ("ma", "并购"), ("strategic_acquisition", "并购"), ("dividend_recovery", "分红回收"), ("asset_sale", "资产出售"), ("equity_transfer", "老股转让")]:
        if has_value(exit_data.get(key)):
            return field(normalize_exit_path(option), "项目资料解析", "中")
    if "IPO" in text or "上市" in text:
        return field("IPO", "系统推断", "中")
    if "并购" in text or "产业方收购" in text:
        return field("并购", "系统推断", "中")
    if "分红" in text:
        return field("分红回收", "系统推断", "中")
    return field("不确定", "缺失", "低", needs_confirmation=True)


def detect_boolean(text: str, keywords: list[str], source: str, manual_value: Any = None) -> dict[str, Any]:
    if manual_value is not None:
        return field(bool(manual_value), "用户手动输入", "中")
    score = keyword_count(text, keywords)
    if score > 0:
        return field(True, source, "高" if score >= 3 else "中")
    return field(False, "缺失", "低", needs_confirmation=True)


def classification_reason(target_type: Any, text: str) -> str:
    reasons = {
        "一级市场融资标的": "识别到融资、估值、股权出让、产品客户或收入等一级市场融资特征。",
        "未上市成长公司": "未识别出强项目/SPV或资产型特征，默认按未上市成长公司处理。",
        "项目公司 / SPV": "识别到项目公司、SPV、项目总投资、建设周期、IRR、回收期或项目现金流等特征。",
        "资产型项目": "识别到资产、资源、牌照、机柜、合同、产能、固定资产或重置成本等资产型特征。",
    }
    return reasons.get(str(target_type), "标的类型需要用户进一步确认。")


def build_warnings(profile: dict[str, Any]) -> list[str]:
    warnings = []
    for key in PROFILE_FIELDS:
        payload = profile.get(key, {})
        if payload.get("confidence") in {"低", "缺失"} or payload.get("needs_confirmation"):
            warnings.append(f"{field_label(key)}仍需人工确认。")
    return warnings


def field(value: Any, source: str, confidence: str, confirmed: Any = None, needs_confirmation: bool | None = None, notes: str = "", source_location: str = "") -> dict[str, Any]:
    detected = "" if value is None else value
    confirmed_value = detected if confirmed is None or confirmed == "" else confirmed
    if needs_confirmation is None:
        needs_confirmation = confidence in {"低", "缺失"} or source in {"系统推断", "缺失", "系统默认"}
    return {
        "detected_value": detected,
        "confirmed_value": confirmed_value,
        "source": source,
        "source_location": source_location,
        "confidence": confidence,
        "needs_confirmation": bool(needs_confirmation),
        "notes": notes,
    }


def empty_field() -> dict[str, Any]:
    return field("", "缺失", "缺失", needs_confirmation=True)


def first_field(candidates: list[tuple[Any, str, str]], manual_value: Any = None) -> dict[str, Any]:
    for value, source, confidence in candidates:
        if has_value(value):
            return field(value, source, confidence, confirmed=manual_value)
    return field("", "缺失", "缺失", confirmed=manual_value, needs_confirmation=True)


def normalize_document_extraction(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    if "extraction" in payload and isinstance(payload["extraction"], dict):
        extraction = dict(payload["extraction"])
        parsed = payload.get("parsed_document", {})
        if parsed.get("file_name"):
            extraction["_source_file"] = parsed.get("file_name")
        return extraction
    return payload


def searchable_text(*payloads: dict[str, Any]) -> str:
    return " ".join(stringify(payload) for payload in payloads if payload)


def stringify(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {stringify(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(stringify(item) for item in value)
    return str(value or "")


def assumption_value(assumption_confirmation: dict[str, Any], group: str, field_name: str) -> Any:
    inputs = assumption_confirmation.get("valuation_inputs", {})
    payload = inputs.get(group, {}).get(field_name)
    if payload and has_value(payload.get("confirmed_value")):
        return payload.get("confirmed_value")
    for item in assumption_confirmation.get("assumption_groups", {}).get(group, []):
        if item.get("field") == field_name and has_value(item.get("confirmed_value")):
            return item.get("confirmed_value")
    return None


def financial_field(financial_extraction: dict[str, Any], field_name: str) -> Any:
    return financial_extraction.get("extracted_financial_data", {}).get("fields", {}).get(field_name, {}).get("extraction_result")


def filename_project_name(file_name: Any) -> str:
    stem = Path(str(file_name or "")).stem
    stem = re.sub(r"^\d{8}_\d{6}_", "", stem)
    stem = re.sub(r"[_\-\s]*(商业计划书|BP|财务模型|财务预测|项目测算表|financial.?model|model)$", "", stem, flags=re.IGNORECASE)
    return stem.strip("_- ")[:80]


def keyword_count(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword and keyword in text)


def first_value(*values: Any) -> Any:
    for value in values:
        if has_value(value):
            return value
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value is not None
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    text = str(value).strip()
    return bool(text) and text not in {"待确认", "未披露", "缺失", "无", "None"}


def normalize_option(value: Any, options: list[str], fallback: str) -> str:
    text = str(value or "").strip()
    if text in options:
        return text
    for option in options:
        if text and (text in option or option in text):
            return option
    return fallback


def normalize_exit_path(value: Any) -> str:
    text = str(value or "")
    if "老股" in text:
        return "不确定"
    if "IPO" in text or "上市" in text:
        return "IPO"
    if "并购" in text or "收购" in text:
        return "并购"
    if "分红" in text:
        return "分红回收"
    if "资产" in text:
        return "资产出售"
    return normalize_option(text, EXIT_PATHS, "不确定")


def parse_percent(value: Any) -> float | None:
    if not has_value(value):
        return None
    text = str(value).replace(",", "").replace("，", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group(0))
    return number / 100 if "%" in text or number > 1 else number


def is_positive_number(value: Any) -> bool:
    if not has_value(value):
        return False
    text = str(value)
    if any(keyword in text for keyword in ["亏损", "负", "-"]):
        return False
    match = re.search(r"\d+(?:\.\d+)?", text.replace(",", "").replace("，", ""))
    return bool(match and float(match.group(0)) > 0)


def field_label(key: str) -> str:
    labels = {
        "target_name": "标的名称",
        "target_type": "标的类型",
        "industry": "所属行业",
        "rachel_ecosystem": "Rachel 战略生态",
        "is_financing_or_secondary_transfer": "融资或老股转让状态",
        "is_complete_company": "完整公司主体判断",
        "is_single_project_spv": "单一项目 / SPV 判断",
        "is_asset_based": "资产型判断",
        "has_revenue": "收入状态",
        "is_profitable": "盈利状态",
        "revenue_growth_status": "收入增长状态",
        "cash_flow_stability": "现金流稳定性",
        "exit_path": "退出路径",
    }
    return labels.get(key, key)
