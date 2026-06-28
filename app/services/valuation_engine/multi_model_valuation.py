from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any

from app.services.valuation_engine.valuation_calculator import format_money, format_range


MODEL_NAME_ALIASES = {
    "资产重估法": "资产重估 / 重置成本法",
    "重置成本法": "资产重估 / 重置成本法",
    "EBITDA倍数法": "EBITDA 倍数法",
}

DEFAULT_WEIGHT_RULES = {
    "未上市成长公司": {
        "收入倍数法": 35,
        "EBITDA 倍数法": 20,
        "利润倍数法": 15,
        "DCF 简化法": 15,
        "订单倍数法": 10,
        "资产重估 / 重置成本法": 5,
    },
    "一级市场融资标的": {
        "收入倍数法": 25,
        "利润倍数法": 20,
        "EBITDA 倍数法": 20,
        "订单倍数法": 15,
        "DCF 简化法": 10,
        "资产重估 / 重置成本法": 10,
    },
    "项目公司 / SPV": {
        "DCF 简化法": 40,
        "IRR / 投资回收期校验": 20,
        "EBITDA 倍数法": 15,
        "资产重估 / 重置成本法": 15,
        "收入倍数法": 10,
    },
    "资产型项目": {
        "资产重估 / 重置成本法": 35,
        "DCF 简化法": 25,
        "EBITDA 倍数法": 15,
        "收入倍数法": 10,
        "IRR / 投资回收期校验": 15,
    },
}


def run_multi_model_comparison(
    valuation_result: dict[str, Any],
    user_weighting: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    target_name = valuation_result.get("target_name") or "未命名项目"
    target_type = infer_target_type(valuation_result)
    model_results = valuation_result.get("model_results", [])
    comparable_models = build_model_comparison(model_results)
    default_table = build_default_weighting_table(comparable_models, target_type)
    weighting_table = apply_user_weighting(default_table, user_weighting)
    weighted_range = build_weighted_valuation_range(weighting_table)
    dispersion = calculate_model_dispersion(weighting_table)
    excluded_models = build_excluded_models(weighting_table, model_results)
    divergence_drivers = identify_divergence_drivers(weighting_table, valuation_result, dispersion)
    sensitivity_notes = build_sensitivity_notes(weighting_table, valuation_result, dispersion)
    confidence_level, confidence_reason = confidence_from_multi_model(
        weighting_table,
        valuation_result,
        weighted_range,
        dispersion,
        divergence_drivers,
    )
    warnings = list(valuation_result.get("warnings", []))
    if weighted_range["included_model_count"] < 2:
        warnings.append("可纳入模型少于 2 个，综合区间置信度较低。")
    if weighted_range["method"] == "no_included_models":
        warnings.append("所有可用模型均被剔除，无法生成加权综合估值区间。")

    return {
        "target_name": target_name,
        "valuation_date": date.today().isoformat(),
        "input_source": valuation_result.get("input_source", "V0.6 基础估值计算结果"),
        "target_type": target_type,
        "model_comparison": comparable_models,
        "weighting_table": weighting_table,
        "weighted_valuation_range": weighted_range,
        "model_dispersion": dispersion,
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
        "major_divergence_drivers": divergence_drivers,
        "excluded_models": excluded_models,
        "sensitivity_notes": sensitivity_notes,
        "warnings": warnings,
        "for_v0_8_decision_memo": {
            "valuation_range": weighted_range,
            "confidence_level": confidence_level,
            "key_assumptions": key_assumptions_from_result(valuation_result),
            "major_risks": divergence_drivers,
            "data_gaps": valuation_result.get("missing_data", []),
            "questions_for_company": questions_from_missing_data(valuation_result.get("missing_data", [])),
            "recommended_research_action": research_action_from_confidence(confidence_level),
        },
    }


def infer_target_type(valuation_result: dict[str, Any]) -> str:
    candidates = [
        valuation_result.get("target_type"),
        valuation_result.get("input_summary", {}).get("target_type"),
        valuation_result.get("input_summary", {}).get("primary_type"),
    ]
    for candidate in candidates:
        text = str(candidate or "")
        if "SPV" in text or "项目公司" in text:
            return "项目公司 / SPV"
        if "资产" in text:
            return "资产型项目"
        if "融资" in text or "一级市场" in text:
            return "一级市场融资标的"
        if "成长" in text:
            return "未上市成长公司"
    return "未上市成长公司"


def build_model_comparison(model_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in model_results:
        model = canonical_model_name(result.get("model", ""))
        range_values = normalized_range_values(result)
        status = result.get("status", "")
        can_include = bool(range_values) and status != "不可计算"
        rows.append(
            {
                "model": model,
                "status": status,
                "input_completeness": result.get("input_completeness", ""),
                "raw_valuation": result.get("raw_valuation", ""),
                "discounted_valuation": result.get("discounted_valuation", ""),
                "confidence": result.get("confidence", ""),
                "basis": result.get("主要依据", ""),
                "limitations": result.get("main_limitations", ""),
                "range_values": range_values,
                "can_include": can_include,
                "exclusion_reason": "" if can_include else exclusion_reason(result),
            }
        )
    return rows


def build_default_weighting_table(model_comparison: list[dict[str, Any]], target_type: str) -> list[dict[str, Any]]:
    rules = DEFAULT_WEIGHT_RULES.get(target_type, DEFAULT_WEIGHT_RULES["未上市成长公司"])
    rows = []
    for row in model_comparison:
        model = row["model"]
        default_weight = rules.get(model, 0)
        include = row["can_include"] and default_weight > 0
        reason = weight_reason(model, target_type, default_weight, row)
        rows.append(
            {
                "model": model,
                "default_weight": float(default_weight),
                "user_weight": float(default_weight),
                "normalized_weight": 0.0,
                "include_in_range": include,
                "weight_reason": reason,
                "model_confidence": row.get("confidence", ""),
                "range_values": row.get("range_values", {}),
                "status": row.get("status", ""),
                "exclusion_reason": "" if include else row.get("exclusion_reason") or "该模型默认不纳入当前标的类型综合区间。",
            }
        )
    return normalize_weighting_table(rows)


def apply_user_weighting(default_table: list[dict[str, Any]], user_weighting: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not user_weighting:
        return default_table
    overrides = {canonical_model_name(row.get("model", "")): row for row in user_weighting}
    rows = []
    for row in default_table:
        updated = {**row}
        override = overrides.get(row["model"])
        if override:
            updated["user_weight"] = to_float(override.get("user_weight", override.get("用户调整权重", row["user_weight"])))
            updated["include_in_range"] = bool(override.get("include_in_range", override.get("是否纳入综合区间", row["include_in_range"])))
            if not updated["include_in_range"]:
                updated["exclusion_reason"] = "用户手动排除。"
        rows.append(updated)
    return normalize_weighting_table(rows)


def normalize_weighting_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    included = [row for row in rows if row.get("include_in_range") and row.get("range_values")]
    total_weight = sum(max(to_float(row.get("user_weight")), 0.0) for row in included)
    if total_weight <= 0:
        total_weight = sum(max(to_float(row.get("default_weight")), 0.0) for row in included)
        for row in included:
            row["user_weight"] = row.get("default_weight", 0)
    for row in rows:
        if row.get("include_in_range") and row.get("range_values") and total_weight > 0:
            row["normalized_weight"] = max(to_float(row.get("user_weight")), 0.0) / total_weight
        else:
            row["normalized_weight"] = 0.0
    return rows


def build_weighted_valuation_range(weighting_table: list[dict[str, Any]]) -> dict[str, Any]:
    included = [row for row in weighting_table if row.get("include_in_range") and row.get("normalized_weight") > 0 and row.get("range_values")]
    if not included:
        return {
            "low": None,
            "base": None,
            "high": None,
            "currency": "万元 RMB",
            "method": "no_included_models",
            "display": "无可纳入模型，暂不生成综合区间。",
            "weight_source": "用户权重 / 默认权重",
            "included_model_count": 0,
            "excluded_model_count": len(weighting_table),
        }
    low = sum(row["range_values"]["low"] * row["normalized_weight"] for row in included)
    base = sum(row["range_values"]["base"] * row["normalized_weight"] for row in included)
    high = sum(row["range_values"]["high"] * row["normalized_weight"] for row in included)
    return {
        "low": low,
        "base": base,
        "high": high,
        "currency": "万元 RMB",
        "method": "weighted_multi_model" if len(included) >= 2 else "single_model_reference",
        "display": format_range(low, base, high),
        "weight_source": "用户调整权重，系统自动归一化" if any(row["user_weight"] != row["default_weight"] for row in included) else "系统默认权重，自动归一化",
        "included_model_count": len(included),
        "excluded_model_count": len(weighting_table) - len(included),
    }


def calculate_model_dispersion(weighting_table: list[dict[str, Any]]) -> dict[str, Any]:
    included_values = [
        row["range_values"]["base"]
        for row in weighting_table
        if row.get("include_in_range") and row.get("range_values") and row["range_values"].get("base") is not None
    ]
    if len(included_values) < 2:
        return {"min_value": None, "max_value": None, "spread_ratio": None, "dispersion_level": "无法判断", "reason": "可纳入模型少于 2 个。"}
    min_value = min(included_values)
    max_value = max(included_values)
    spread_ratio = max_value / min_value if min_value > 0 else None
    return {
        "min_value": min_value,
        "max_value": max_value,
        "spread_ratio": spread_ratio,
        "dispersion_level": dispersion_level(spread_ratio),
        "reason": dispersion_reason(spread_ratio),
    }


def identify_divergence_drivers(
    weighting_table: list[dict[str, Any]],
    valuation_result: dict[str, Any],
    dispersion: dict[str, Any],
) -> list[str]:
    drivers: list[str] = []
    if dispersion.get("dispersion_level") in {"高", "极高"}:
        drivers.append("不同模型 base 估值差异较大，需要核验收入、利润、现金流和资产口径。")
    dcf_base = model_base(weighting_table, "DCF 简化法")
    multiple_bases = [
        row["range_values"]["base"]
        for row in weighting_table
        if row["model"] in {"收入倍数法", "利润倍数法", "EBITDA 倍数法", "订单倍数法"} and row.get("range_values")
    ]
    if dcf_base and multiple_bases and dcf_base < median(multiple_bases) * 0.75:
        drivers.append("DCF 结果显著低于倍数法，需检查现金流、折现率和终值假设。")
    asset_base = model_base(weighting_table, "资产重估 / 重置成本法")
    if asset_base and dcf_base and asset_base > dcf_base * 1.25:
        drivers.append("资产重估结果高于现金流估值，需核验资产权属、重置成本和可交易性。")
    missing_text = "、".join(valuation_result.get("missing_data", []))
    if "CAPEX" in missing_text or "项目总投资" in missing_text:
        drivers.append("CAPEX 或项目总投资缺失，影响项目现金流和资产型模型解释力。")
    if "现金流" in missing_text:
        drivers.append("现金流数据缺失或不足，DCF 和回收期校验置信度受限。")
    if "流动性折扣" in missing_text or has_no_applied_discount(valuation_result):
        drivers.append("流动性折扣未充分设置，非公开市场估值需要人工确认折扣假设。")
    if "团队风险" in missing_text:
        drivers.append("团队风险数据不足，可能影响风险折扣和估值可用性。")
    return dedupe(drivers) or ["当前模型分歧来源暂不显著，但仍需人工核验关键假设。"]


def confidence_from_multi_model(
    weighting_table: list[dict[str, Any]],
    valuation_result: dict[str, Any],
    weighted_range: dict[str, Any],
    dispersion: dict[str, Any],
    divergence_drivers: list[str],
) -> tuple[str, str]:
    included_count = weighted_range.get("included_model_count", 0)
    readiness = valuation_result.get("input_summary", {}).get("valuation_readiness_level", "不足")
    dispersion_level_value = dispersion.get("dispersion_level", "无法判断")
    missing_count = len(valuation_result.get("missing_data", []))
    has_cashflow = any(row["model"] == "DCF 简化法" and row.get("include_in_range") for row in weighting_table)
    has_fundamental = any(row["model"] in {"收入倍数法", "利润倍数法", "EBITDA 倍数法"} and row.get("include_in_range") for row in weighting_table)

    if included_count <= 1 or dispersion_level_value == "极高" or readiness == "不足":
        return "仅供框架参考", "可纳入模型不足、模型分歧极高或 V0.5 准备度不足，当前只能作为估值框架参考。"
    if included_count >= 3 and readiness == "高" and dispersion_level_value in {"低", "中"} and has_cashflow and has_fundamental and missing_count <= 3:
        return "高", "至少 3 个模型可纳入，包含现金流和基础经营数据，且模型分歧可控。"
    if included_count >= 2 and dispersion_level_value in {"低", "中", "无法判断"} and missing_count <= 8:
        return "中", "已有多个模型可交叉验证，但仍需确认部分核心假设。"
    return "低", "模型数量、数据完整度或分歧度仍限制综合区间可靠性。"


def build_sensitivity_notes(
    weighting_table: list[dict[str, Any]],
    valuation_result: dict[str, Any],
    dispersion: dict[str, Any],
) -> list[str]:
    notes = list(valuation_result.get("sensitivity_notes", []))
    if any(row["model"] == "收入倍数法" and row.get("include_in_range") for row in weighting_table):
        notes.append("收入倍数法权重越高，综合区间越依赖预测收入和可比倍数。")
    if any(row["model"] == "DCF 简化法" and row.get("include_in_range") for row in weighting_table):
        notes.append("DCF 权重越高，综合区间越依赖现金流、折现率、预测期和退出价值假设。")
    if dispersion.get("dispersion_level") in {"高", "极高"}:
        notes.append("模型分歧较高时，不宜机械使用加权结果，应优先解释差异来源。")
    return dedupe(notes) or ["请调整模型权重并补充关键假设，观察综合区间的敏感性变化。"]


def build_excluded_models(weighting_table: list[dict[str, Any]], model_results: list[dict[str, Any]]) -> list[dict[str, str]]:
    known_models = {row["model"] for row in weighting_table}
    excluded = [
        {"model": row["model"], "reason": row.get("exclusion_reason", "未纳入综合区间。")}
        for row in weighting_table
        if not row.get("include_in_range")
    ]
    for result in model_results:
        model = canonical_model_name(result.get("model", ""))
        if model not in known_models:
            excluded.append({"model": model, "reason": exclusion_reason(result)})
    return excluded


def normalized_range_values(result: dict[str, Any]) -> dict[str, float]:
    values = result.get("discounted_range_values") or result.get("range_values") or {}
    low = to_float_or_none(values.get("low"))
    base = to_float_or_none(values.get("base"))
    high = to_float_or_none(values.get("high"))
    if base is None:
        available = [value for value in [low, high] if value is not None]
        base = median(available) if available else None
    if low is None:
        low = base
    if high is None:
        high = base
    if low is None or base is None or high is None:
        return {}
    return {"low": low, "base": base, "high": high}


def canonical_model_name(model: str) -> str:
    return MODEL_NAME_ALIASES.get(model, model)


def exclusion_reason(result: dict[str, Any]) -> str:
    if result.get("status") == "不可计算":
        missing = "、".join(result.get("missing_fields", []))
        return f"不可计算，缺少必要输入：{missing}" if missing else "不可计算。"
    if not result.get("range_values"):
        return "缺少 low/base/high 区间，无法纳入综合区间。"
    return "默认不纳入综合区间。"


def weight_reason(model: str, target_type: str, default_weight: float, row: dict[str, Any]) -> str:
    if not row.get("can_include"):
        return row.get("exclusion_reason", "模型数据不足。")
    if default_weight <= 0:
        return f"{target_type} 默认权重规则中不优先使用该模型。"
    return f"{target_type} 默认权重规则，结合模型可计算性和置信度。"


def dispersion_level(spread_ratio: float | None) -> str:
    if spread_ratio is None:
        return "无法判断"
    if spread_ratio < 1.5:
        return "低"
    if spread_ratio < 2.5:
        return "中"
    if spread_ratio < 4:
        return "高"
    return "极高"


def dispersion_reason(spread_ratio: float | None) -> str:
    if spread_ratio is None:
        return "最低模型估值不大于 0 或可纳入模型不足。"
    return f"最高模型 base 估值约为最低模型的 {spread_ratio:.2f} 倍。"


def model_base(weighting_table: list[dict[str, Any]], model: str) -> float | None:
    for row in weighting_table:
        if row["model"] == model and row.get("range_values"):
            return row["range_values"].get("base")
    return None


def has_no_applied_discount(valuation_result: dict[str, Any]) -> bool:
    risk_adjustments = valuation_result.get("risk_adjustments", [])
    return not risk_adjustments or all(row.get("是否应用") != "是" for row in risk_adjustments)


def key_assumptions_from_result(valuation_result: dict[str, Any]) -> list[str]:
    summary = valuation_result.get("input_summary", {})
    groups = summary.get("input_groups", {})
    assumptions = []
    for group, fields in groups.items():
        if fields:
            assumptions.append(f"{group}: {', '.join(fields[:6])}")
    return assumptions


def questions_from_missing_data(missing_data: list[str]) -> list[str]:
    return [f"请补充并确认：{item}。" for item in missing_data[:12]]


def research_action_from_confidence(confidence_level: str) -> str:
    if confidence_level == "高":
        return "进入深度研究"
    if confidence_level == "中":
        return "需要补充数据"
    if confidence_level == "低":
        return "等待更多财务或项目数据"
    return "暂不进入估值"


def format_weight(weight: float) -> str:
    return f"{weight:.1%}"


def display_range_values(values: dict[str, Any]) -> str:
    return format_range(values.get("low"), values.get("base"), values.get("high")) if values else ""


def display_money(value: float | None) -> str:
    return format_money(value)


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def to_float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
