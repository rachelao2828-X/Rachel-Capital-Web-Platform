from __future__ import annotations

from dataclasses import dataclass

from app.services.valuation_engine.model_registry import dedupe, model_row


@dataclass(frozen=True)
class ListedCompanyProfile:
    stock_name: str
    ticker: str
    market: str
    industry: str
    ecosystem: str
    is_profitable: bool
    revenue_growth_status: str
    profit_growth_status: str
    asset_attribute: str
    cash_flow_stability: str
    is_strong_cycle: bool
    is_sotp_suitable: bool
    is_turnaround: bool


@dataclass(frozen=True)
class ListedValuationResult:
    portrait: list[str]
    primary_models: list[str]
    auxiliary_models: list[str]
    reference_models: list[str]
    unsuitable_models: list[str]
    comparison_table: list[dict[str, str]]
    data_requirements: list[str]
    valuation_framework: list[str]
    risks: list[str]
    research_action: str


def analyze_listed_company(profile: ListedCompanyProfile) -> ListedValuationResult:
    primary: list[str] = []
    auxiliary: list[str] = []
    reference: list[str] = []
    unsuitable: list[str] = []
    reasons: dict[str, str] = {}

    if profile.is_profitable and profile.profit_growth_status in {"高增长", "稳定增长"}:
        add(primary, reasons, ["PE", "PEG", "DCF", "EV/EBITDA", "历史估值分位", "同业比较"], "公司已有盈利且利润增长较清晰，适合用盈利和现金流框架交叉验证。")

    if profile.revenue_growth_status == "高增长" and profile.profit_growth_status in {"周期波动", "亏损"}:
        add(primary, reasons, ["PS", "EV/Sales", "远期 PE", "PEG", "情景估值", "同业比较"], "收入高增长但盈利波动，估值应优先观察收入扩张和远期盈利兑现。")

    if profile.is_strong_cycle or profile.revenue_growth_status == "周期波动" or profile.profit_growth_status == "周期波动":
        add(primary, reasons, ["PB", "周期归一化PE", "EV/EBITDA", "历史周期分位", "资产重估法"], "标的具备周期属性，应弱化单一年份利润，关注资产底部、周期中枢和历史周期分位。")

    if profile.asset_attribute == "重资产":
        add(primary, reasons, ["PB", "EV/EBITDA", "ROE-PB", "订单利润法"], "重资产制造公司需要结合资产回报、订单兑现和企业价值倍数。")
        add(auxiliary, reasons, ["DCF"], "DCF 可作为现金流辅助模型，但参数敏感度较高。")

    if profile.asset_attribute == "平台型" or profile.is_sotp_suitable:
        add(primary, reasons, ["SOTP", "PE", "PS", "DCF", "用户价值法", "同业比较"], "平台型或多业务公司适合拆分业务线，使用 SOTP 与经营指标交叉验证。")

    if profile.asset_attribute == "资源型":
        add(primary, reasons, ["PB", "EV/EBITDA", "资源储量估值", "周期归一化利润", "资产重估法"], "资源型公司价值受资源储量、价格周期和资产重估影响较大。")

    if profile.asset_attribute == "金融型":
        add(primary, reasons, ["PB", "ROE-PB", "历史估值分位", "同业比较"], "金融型公司更适合用净资产、ROE 和历史估值区间观察。")

    if profile.is_turnaround:
        add(auxiliary, reasons, ["情景估值", "历史估值分位", "资产重估法"], "困境修复需要用情景和资产底线观察，不宜只看当前利润。")

    if not primary:
        add(primary, reasons, ["同业比较", "历史估值分位", "情景估值"], "当前画像信息不足，先建立公开市场参照框架。")

    if profile.cash_flow_stability == "稳定" and "DCF" not in primary:
        add(auxiliary, reasons, ["DCF"], "现金流稳定时可补充 DCF 作为内在价值视角。")
    if profile.cash_flow_stability == "不稳定":
        add(reference, reasons, ["DCF"], "现金流不稳定，DCF 暂作参考模型。")

    if not profile.is_profitable:
        add(unsuitable, reasons, ["PE"], "当前未盈利，静态 PE 不适合作为主模型。")
    if profile.profit_growth_status == "亏损":
        add(unsuitable, reasons, ["PEG"], "利润为亏损状态时 PEG 解释力较弱。")
    if profile.asset_attribute not in {"重资产", "资源型", "金融型"} and not profile.is_strong_cycle:
        add(reference, reasons, ["PB"], "PB 可作底部资产参照，但不宜作为核心模型。")

    primary = dedupe(primary)
    auxiliary = [item for item in dedupe(auxiliary) if item not in primary]
    reference = [item for item in dedupe(reference) if item not in primary and item not in auxiliary]
    unsuitable = [item for item in dedupe(unsuitable) if item not in primary and item not in auxiliary and item not in reference]
    table = build_table(primary, auxiliary, reference, unsuitable, reasons)
    return ListedValuationResult(
        portrait=build_portrait(profile),
        primary_models=primary,
        auxiliary_models=auxiliary,
        reference_models=reference,
        unsuitable_models=unsuitable,
        comparison_table=table,
        data_requirements=build_data_requirements(profile, primary + auxiliary),
        valuation_framework=build_framework(profile, primary),
        risks=build_risks(profile),
        research_action=research_action(profile),
    )


def add(target: list[str], reasons: dict[str, str], models: list[str], reason: str) -> None:
    for model in models:
        target.append(model)
        reasons.setdefault(model, reason)


def build_table(primary: list[str], auxiliary: list[str], reference: list[str], unsuitable: list[str], reasons: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(model_row(model, "高", reasons.get(model, ""), "主模型") for model in primary)
    rows.extend(model_row(model, "中", reasons.get(model, ""), "辅助模型") for model in auxiliary)
    rows.extend(model_row(model, "低", reasons.get(model, ""), "参考模型") for model in reference)
    rows.extend(model_row(model, "不适用", reasons.get(model, ""), "不建议使用") for model in unsuitable)
    return rows


def build_portrait(profile: ListedCompanyProfile) -> list[str]:
    portrait = [
        f"市场：{profile.market}",
        f"行业：{profile.industry or '待补充'}",
        f"战略生态：{profile.ecosystem}",
        f"资产属性：{profile.asset_attribute}",
        f"收入增长：{profile.revenue_growth_status}",
        f"利润增长：{profile.profit_growth_status}",
        f"现金流稳定性：{profile.cash_flow_stability}",
    ]
    if profile.is_strong_cycle:
        portrait.append("具备强周期特征")
    if profile.is_sotp_suitable:
        portrait.append("适合 SOTP 分部估值")
    if profile.is_turnaround:
        portrait.append("处于困境反转或修复观察阶段")
    return portrait


def build_data_requirements(profile: ListedCompanyProfile, models: list[str]) -> list[str]:
    data = [
        "最近三年收入、净利润、毛利率、ROE、经营现金流",
        "当前市值、企业价值、净债务、股本结构",
        "可比公司估值倍数和核心经营指标",
        "历史估值分位和行业周期位置",
    ]
    if "SOTP" in models:
        data.append("分业务收入、利润、资产和可比公司倍数")
    if profile.is_strong_cycle:
        data.append("跨周期利润中枢、周期高低点和订单/价格周期数据")
    if profile.asset_attribute == "资源型":
        data.append("资源储量、产量、价格假设和单位成本")
    if profile.asset_attribute == "重资产":
        data.append("资本开支、折旧、产能利用率和订单兑现节奏")
    return dedupe(data)


def build_framework(profile: ListedCompanyProfile, primary_models: list[str]) -> list[str]:
    return [
        f"以 {profile.asset_attribute} 和 {profile.revenue_growth_status} 为核心画像建立估值框架。",
        f"先使用 {', '.join(primary_models[:4])} 形成主模型交叉验证。",
        "再补充同业、历史区间和情景假设，形成估值区间而非单点结论。",
        "后续需要补齐财务、行业周期、同业样本和业务分部数据。",
    ]


def build_risks(profile: ListedCompanyProfile) -> list[str]:
    risks = ["财务数据口径和一次性项目影响", "行业景气和市场估值波动", "同业可比性不足"]
    if profile.is_strong_cycle:
        risks.append("周期位置误判")
    if profile.is_turnaround:
        risks.append("困境修复进度低于预期")
    if profile.cash_flow_stability == "不稳定":
        risks.append("现金流波动导致 DCF 假设敏感")
    return risks


def research_action(profile: ListedCompanyProfile) -> str:
    if profile.industry and profile.ticker:
        return "进入深度研究"
    return "需要补充数据"
