from __future__ import annotations

from dataclasses import dataclass

from app.services.valuation_engine.model_registry import dedupe, model_row


@dataclass(frozen=True)
class PrivateMarketProfile:
    target_name: str
    initial_type: str
    industry: str
    ecosystem: str
    is_financing_or_transfer: bool
    is_complete_company: bool
    is_single_project_spv: bool
    is_asset_or_contract_based: bool
    has_revenue: bool
    is_profitable: bool
    revenue_growth_status: str
    cash_flow_stable: bool
    exit_path: str
    financing_round: str | None = None
    pre_money_valuation: str | None = None
    post_money_valuation: str | None = None
    financing_amount: str | None = None
    equity_sold: str | None = None
    previous_round_valuation: str | None = None
    previous_round_date: str | None = None
    project_total_investment: str | None = None
    construction_period: str | None = None
    expected_revenue: str | None = None
    expected_gross_margin: str | None = None
    expected_net_margin: str | None = None
    annual_cash_flow: str | None = None
    payback_period: str | None = None
    government_subsidy: str | None = None
    key_contract_signed: bool | None = None
    utilization_rate: str | None = None
    asset_type: str | None = None
    book_value: str | None = None
    replacement_cost: str | None = None
    comparable_transaction_price: str | None = None
    asset_generates_cash_flow: bool | None = None
    asset_is_scarce: bool | None = None
    asset_is_tradeable: bool | None = None
    asset_has_long_contract: bool | None = None
    asset_has_policy_restriction: bool | None = None


@dataclass(frozen=True)
class PrivateMarketClassification:
    primary_type: str
    secondary_types: list[str]
    reasons: list[str]


@dataclass(frozen=True)
class PrivateMarketValuationResult:
    classification: PrivateMarketClassification
    portrait: list[str]
    primary_models: list[str]
    auxiliary_models: list[str]
    reference_models: list[str]
    unsuitable_models: list[str]
    required_adjustments: list[str]
    comparison_table: list[dict[str, str]]
    data_requirements: list[str]
    valuation_framework: list[str]
    risks: list[str]
    research_action: str


def analyze_private_market(profile: PrivateMarketProfile) -> PrivateMarketValuationResult:
    classification = classify_private_market(profile)
    primary, auxiliary, reference, unsuitable, adjustments, reasons = recommend_private_models(profile, classification)
    table = build_table(primary, auxiliary, reference, unsuitable, reasons)
    return PrivateMarketValuationResult(
        classification=classification,
        portrait=build_portrait(profile),
        primary_models=primary,
        auxiliary_models=auxiliary,
        reference_models=reference,
        unsuitable_models=unsuitable,
        required_adjustments=adjustments,
        comparison_table=table,
        data_requirements=build_data_requirements(profile, classification),
        valuation_framework=build_framework(profile, classification, primary),
        risks=build_risks(profile, classification),
        research_action=research_action(profile, classification),
    )


def classify_private_market(profile: PrivateMarketProfile) -> PrivateMarketClassification:
    matched: list[str] = []
    reasons: list[str] = []
    if profile.initial_type != "不确定，让系统判断":
        matched.append(profile.initial_type)
        reasons.append(f"用户初选类型为：{profile.initial_type}。")
    if profile.is_single_project_spv:
        matched.append("项目公司 / SPV")
        reasons.append("标的是单一项目或 SPV，应优先按项目现金流和回收期建立框架。")
    if profile.is_asset_or_contract_based:
        matched.append("资产型项目")
        reasons.append("标的主要依赖资产、资源、牌照或合同，需要加入资产价值视角。")
    if profile.is_financing_or_transfer:
        matched.append("一级市场融资标的")
        reasons.append("标的处于融资或老股转让场景，需要评估本轮交易定价。")
    if profile.is_complete_company and not profile.is_single_project_spv:
        matched.append("未上市成长公司")
        reasons.append("标的是完整公司主体，可建立整体公司估值框架。")
    if not matched:
        matched.append("未上市成长公司")
        reasons.append("信息不足，暂按未上市成长公司建立初步框架。")

    matched = dedupe(matched)
    primary = choose_primary(matched)
    secondary = [item for item in matched if item != primary]
    return PrivateMarketClassification(primary_type=primary, secondary_types=secondary, reasons=reasons)


def choose_primary(matched: list[str]) -> str:
    for candidate in ["项目公司 / SPV", "一级市场融资标的", "资产型项目", "未上市成长公司"]:
        if candidate in matched:
            return candidate
    return matched[0]


def recommend_private_models(profile: PrivateMarketProfile, classification: PrivateMarketClassification):
    primary: list[str] = []
    auxiliary: list[str] = []
    reference: list[str] = []
    unsuitable: list[str] = []
    adjustments: list[str] = []
    reasons: dict[str, str] = {}
    type_names = [classification.primary_type] + classification.secondary_types

    if "未上市成长公司" in type_names:
        add(primary if classification.primary_type == "未上市成长公司" else auxiliary, reasons, ["可比上市公司法", "可比融资交易法", "收入倍数", "ARR 倍数", "用户价值法", "SOTP", "二级市场映射法"], "未上市成长公司需要用公开市场、融资交易和经营指标交叉映射。")
        add(adjustments, reasons, ["流动性折扣", "上市概率折扣", "信息透明度折扣"], "非公开公司需要考虑流动性、退出概率和信息透明度。")
    if "一级市场融资标的" in type_names:
        add(primary if classification.primary_type == "一级市场融资标的" else auxiliary, reasons, ["可比融资交易法", "可比上市公司法", "融资轮次估值锚", "收入倍数", "利润倍数", "ARR 倍数", "订单倍数", "IPO / 并购退出倒推"], "融资或老股交易场景应以交易定价、轮次锚和退出倒推为核心。")
        add(adjustments, reasons, ["技术成熟度折扣", "流动性折扣", "退出路径折扣", "下一轮融资估值推演"], "一级市场交易需要显式考虑技术、流动性、退出和下轮融资风险。")
    if "项目公司 / SPV" in type_names:
        add(primary if classification.primary_type == "项目公司 / SPV" else auxiliary, reasons, ["DCF", "IRR", "投资回收期", "项目现金流模型", "合同现金流法", "产能价值法"], "项目公司核心价值来自项目现金流、合同、产能和回收期。")
        add(adjustments, reasons, ["利用率敏感性", "融资结构敏感性", "政府补贴敏感性", "关键合同风险"], "项目回报对利用率、融资结构、补贴和关键合同高度敏感。")
    if "资产型项目" in type_names:
        add(primary if classification.primary_type == "资产型项目" else auxiliary, reasons, ["资产重估法", "重置成本法", "DCF", "单位产能估值", "资源储量估值", "租金 / 合同现金流估值", "可交易资产比较法"], "资产型项目应先看资产本身、重置成本、现金流和可交易参照。")
        add(adjustments, reasons, ["资产可交易性", "政策限制", "现金流稳定性", "折旧与维护成本"], "资产价值需要被可交易性、政策约束和维护成本修正。")

    if not profile.has_revenue:
        add(unsuitable, reasons, ["收入倍数", "利润倍数", "ARR 倍数"], "尚无收入时，收入或利润倍数不适合作为主模型。")
    if not profile.is_profitable:
        add(reference, reasons, ["利润倍数"], "暂未盈利时，利润倍数只适合作为远期参考。")
    if profile.cash_flow_stable:
        add(auxiliary, reasons, ["DCF", "合同现金流法"], "现金流较稳定时，可加强现金流模型权重。")

    primary = dedupe(primary)
    adjustments = dedupe(adjustments)
    auxiliary = [item for item in dedupe(auxiliary + adjustments) if item not in primary]
    reference = [item for item in dedupe(reference) if item not in primary and item not in auxiliary]
    unsuitable = [item for item in dedupe(unsuitable) if item not in primary and item not in auxiliary and item not in reference]
    return primary, auxiliary, reference, unsuitable, adjustments, reasons


def add(target: list[str], reasons: dict[str, str], items: list[str], reason: str) -> None:
    for item in items:
        target.append(item)
        reasons.setdefault(item, reason)


def build_table(primary: list[str], auxiliary: list[str], reference: list[str], unsuitable: list[str], reasons: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(model_row(model, "高", reasons.get(model, ""), "主模型") for model in primary)
    rows.extend(model_row(model, "中", reasons.get(model, ""), "辅助模型") for model in auxiliary)
    rows.extend(model_row(model, "低", reasons.get(model, ""), "参考模型") for model in reference)
    rows.extend(model_row(model, "不适用", reasons.get(model, ""), "不建议使用") for model in unsuitable)
    return rows


def build_portrait(profile: PrivateMarketProfile) -> list[str]:
    return [
        f"行业：{profile.industry or '待补充'}",
        f"战略生态：{profile.ecosystem}",
        f"收入增长：{profile.revenue_growth_status}",
        f"退出路径：{profile.exit_path}",
        f"正在融资或老股转让：{'是' if profile.is_financing_or_transfer else '否'}",
        f"完整公司主体：{'是' if profile.is_complete_company else '否'}",
        f"单一项目 / SPV：{'是' if profile.is_single_project_spv else '否'}",
        f"依赖资产、资源、牌照或合同：{'是' if profile.is_asset_or_contract_based else '否'}",
    ]


def build_data_requirements(profile: PrivateMarketProfile, classification: PrivateMarketClassification) -> list[str]:
    data = ["公司或项目主体资料、股权结构、历史融资和核心经营数据", "可比上市公司和可比交易样本", "退出路径和时间假设"]
    type_names = [classification.primary_type] + classification.secondary_types
    if "一级市场融资标的" in type_names:
        data.extend(["本轮投前/投后估值、融资金额、出让比例、上一轮估值和融资时间", "技术成熟度、客户验证、订单和里程碑完成情况"])
    if "项目公司 / SPV" in type_names:
        data.extend(["项目总投资、建设周期、收入、利润率、年现金流和回收期", "关键合同、政府补贴、利用率/上架率/负荷率、融资结构"])
    if "资产型项目" in type_names:
        data.extend(["资产权属、账面价值、重置成本、可比交易、可交易限制", "长期合同、政策限制、维护成本和现金流稳定性"])
    if "未上市成长公司" in type_names:
        data.extend(["收入、ARR、客户数量、毛利率、留存率、获客成本", "上市或并购可行性、流动性限制和信息披露质量"])
    return dedupe(data)


def build_framework(profile: PrivateMarketProfile, classification: PrivateMarketClassification, primary_models: list[str]) -> list[str]:
    return [
        f"先按主分类“{classification.primary_type}”建立估值框架，再用辅助分类修正估值边界。",
        f"主模型优先使用：{', '.join(primary_models[:5])}。",
        "必须显式列出折扣、敏感性因素和退出路径假设。",
        "当前阶段只形成研究框架，不输出单点估值结论。",
    ]


def build_risks(profile: PrivateMarketProfile, classification: PrivateMarketClassification) -> list[str]:
    risks = ["信息披露不足和数据可验证性风险", "可比交易样本不足", "退出路径不确定"]
    if "项目公司 / SPV" in [classification.primary_type] + classification.secondary_types:
        risks.extend(["建设进度、利用率、融资成本和关键合同风险"])
    if "资产型项目" in [classification.primary_type] + classification.secondary_types:
        risks.extend(["资产权属、政策限制、可交易性和维护成本风险"])
    if profile.is_financing_or_transfer:
        risks.append("本轮交易条款和下轮融资不确定")
    return dedupe(risks)


def research_action(profile: PrivateMarketProfile, classification: PrivateMarketClassification) -> str:
    if not profile.has_revenue and classification.primary_type not in {"项目公司 / SPV", "资产型项目"}:
        return "需要补充数据"
    if classification.primary_type in {"项目公司 / SPV", "一级市场融资标的"}:
        return "进入深度研究"
    return "进入观察池"
