from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any


TARGET_TYPES = {
    "listed_company": "上市公司",
    "private_growth_company": "未上市成长公司",
    "primary_market_deal": "一级市场融资标的",
    "project_spv": "项目公司 / SPV",
    "asset_project": "资产型项目",
}

ECOSYSTEM_OPTIONS = [
    "AI基础设施生态",
    "半导体生态",
    "华为生态",
    "机器人生态",
    "高端材料生态",
    "船舶与国防生态",
    "医疗科技生态",
    "中国关键技术攻关长期跟踪",
]

MARKET_OPTIONS = ["A股", "港股", "美股", "未上市", "项目型"]
GROWTH_OPTIONS = ["高增长", "稳定增长", "周期波动", "尚无收入"]
EXIT_OPTIONS = ["IPO", "并购", "分红回收", "资产出售", "不确定"]


@dataclass(frozen=True)
class TargetProfile:
    target_name: str
    is_listed: bool
    market: str
    is_financing_or_transaction: bool
    is_complete_company: bool
    is_single_project_spv: bool
    is_asset_or_resource_based: bool
    has_revenue: bool
    is_profitable: bool
    revenue_growth_status: str
    cash_flow_stable: bool
    ecosystem: str
    exit_path: str


@dataclass(frozen=True)
class ClassificationResult:
    primary_type: str
    auxiliary_types: list[str]
    reasons: list[str]


@dataclass(frozen=True)
class RecommendationResult:
    primary_models: list[str]
    auxiliary_models: list[str]
    unsuitable_models: list[str]
    rationale: str
    comparison_table: list[dict[str, str]]
    data_requirements: list[str]


MODEL_CATALOG: dict[str, dict[str, str]] = {
    "PE": {
        "type": "相对估值",
        "data": "净利润、可比公司 PE、盈利质量",
        "output": "合理市值或目标估值区间",
        "note": "适合盈利较稳定的上市公司。",
    },
    "周期归一化 PE": {
        "type": "相对估值",
        "data": "跨周期利润、行业周期位置、历史利润中枢",
        "output": "周期平滑后的估值区间",
        "note": "适合船舶、材料、设备等周期波动行业。",
    },
    "PB": {
        "type": "资产/相对估值",
        "data": "净资产、ROE、历史 PB、同业 PB",
        "output": "基于账面资产和 ROE 的估值区间",
        "note": "适合重资产、金融、周期和资产重估场景。",
    },
    "PS": {
        "type": "相对估值",
        "data": "收入、收入增长、同业 PS",
        "output": "基于收入规模的估值区间",
        "note": "适合尚未稳定盈利但收入可验证的公司。",
    },
    "EV/EBITDA": {
        "type": "企业价值倍数",
        "data": "EV、EBITDA、净债务、同业倍数",
        "output": "企业价值和权益价值区间",
        "note": "适合资本结构差异较大的公司或重资产公司。",
    },
    "DCF": {
        "type": "现金流估值",
        "data": "收入、利润率、资本开支、营运资本、折现率",
        "output": "内在价值区间",
        "note": "适合现金流可建模的公司、项目或资产。",
    },
    "PEG": {
        "type": "成长估值",
        "data": "PE、利润增速、成长持续性",
        "output": "成长调整后的估值合理性",
        "note": "适合盈利增长较清晰的成长型上市公司。",
    },
    "SOTP": {
        "type": "分部估值",
        "data": "业务分部、各分部收入利润、可比倍数",
        "output": "分部加总估值",
        "note": "适合多业务平台型公司或资产组合。",
    },
    "历史估值分位": {
        "type": "市场定价参考",
        "data": "历史 PE/PB/PS/EV 倍数、分位数",
        "output": "当前位置相对历史区间",
        "note": "仅用于市场定价参照，不等同于内在价值。",
    },
    "同业比较": {
        "type": "相对估值",
        "data": "同业公司、财务指标、增长和利润率差异",
        "output": "相对估值区间",
        "note": "适合可比公司较清晰的公司或资产。",
    },
    "情景估值": {
        "type": "情景分析",
        "data": "乐观/中性/保守假设、关键变量",
        "output": "多情景估值区间",
        "note": "适合高不确定性标的。",
    },
    "可比上市公司法": {
        "type": "相对估值",
        "data": "可比上市公司、收入/利润/用户等指标",
        "output": "按公开市场映射的估值区间",
        "note": "适合未上市公司和一级市场交易。",
    },
    "可比融资交易法": {
        "type": "交易估值",
        "data": "可比融资轮次、交易估值、业务阶段",
        "output": "按交易市场映射的估值区间",
        "note": "适合融资、老股转让和一级市场交易。",
    },
    "收入倍数": {
        "type": "成长估值",
        "data": "收入、收入增速、毛利率、同业收入倍数",
        "output": "收入维度估值区间",
        "note": "适合收入可验证但利润尚不稳定的公司。",
    },
    "ARR 倍数": {
        "type": "SaaS/订阅估值",
        "data": "ARR、净收入留存、毛利率、流失率",
        "output": "订阅业务估值区间",
        "note": "适合 SaaS、云服务和订阅型公司。",
    },
    "用户价值法": {
        "type": "用户资产估值",
        "data": "用户数、ARPU、留存、获客成本、生命周期价值",
        "output": "用户资产估值参考",
        "note": "适合平台、消费互联网和 AI 应用。",
    },
    "流动性折扣": {
        "type": "折扣调整",
        "data": "退出路径、交易限制、可售时间",
        "output": "非流动性调整后的估值",
        "note": "适合未上市股权、老股交易和项目股权。",
    },
    "上市概率折扣": {
        "type": "折扣调整",
        "data": "IPO路径、监管环境、财务成熟度、时间表",
        "output": "按退出概率调整后的估值",
        "note": "适合 Pre-IPO 和成长型未上市公司。",
    },
    "二级市场映射法": {
        "type": "映射估值",
        "data": "二级可比公司、生态链映射、估值倍数",
        "output": "二级市场可比估值参考",
        "note": "适合未上市科技公司和产业映射研究。",
    },
    "融资轮次估值锚": {
        "type": "交易锚定",
        "data": "历史轮次估值、本轮条款、稀释比例",
        "output": "轮次定价合理性参考",
        "note": "适合正在融资或老股交易的标的。",
    },
    "利润倍数": {
        "type": "相对估值",
        "data": "净利润、利润率、同业利润倍数",
        "output": "利润维度估值区间",
        "note": "适合已有利润但未上市的公司或交易。",
    },
    "订单倍数": {
        "type": "订单估值",
        "data": "在手订单、确认周期、毛利率、履约风险",
        "output": "订单支撑估值参考",
        "note": "适合设备、工程、项目型公司。",
    },
    "技术成熟度折扣": {
        "type": "风险折扣",
        "data": "技术阶段、客户验证、量产状态、替代风险",
        "output": "技术风险调整后的估值",
        "note": "适合硬科技和早期技术公司。",
    },
    "退出路径折扣": {
        "type": "折扣调整",
        "data": "IPO/并购/回购/分红路径和概率",
        "output": "退出风险调整后的估值",
        "note": "适合一级市场交易。",
    },
    "下轮融资估值推演": {
        "type": "融资推演",
        "data": "本轮估值、资金使用、里程碑、下轮预期",
        "output": "下轮估值和稀释情景",
        "note": "适合融资交易判断。",
    },
    "IPO / 并购退出倒推": {
        "type": "退出倒推",
        "data": "退出估值、时间、折现率、成功概率",
        "output": "当前可接受估值区间",
        "note": "适合一级市场和 Pre-IPO 交易。",
    },
    "IRR": {
        "type": "项目收益",
        "data": "投资额、年度现金流、退出价值、时间",
        "output": "项目内部收益率",
        "note": "适合项目公司、SPV 和资产项目。",
    },
    "投资回收期": {
        "type": "项目收益",
        "data": "初始投资、年度净现金流",
        "output": "静态/动态回收期",
        "note": "适合现金流回收型项目。",
    },
    "项目现金流模型": {
        "type": "项目模型",
        "data": "建设期、产能、利用率、价格、成本、税费、融资结构",
        "output": "项目年度现金流和估值框架",
        "note": "适合项目公司和 SPV。",
    },
    "资产价值法": {
        "type": "资产估值",
        "data": "资产清单、可交易价格、折旧、稀缺性",
        "output": "资产基础价值",
        "note": "适合资产型项目和 SPV。",
    },
    "产能价值法": {
        "type": "产能估值",
        "data": "有效产能、单位产能价值、利用率",
        "output": "按产能计算的资产价值",
        "note": "适合数据中心、工厂、矿山、回收产线。",
    },
    "合同现金流法": {
        "type": "合同估值",
        "data": "合同期限、价格、回款、违约风险",
        "output": "合同现金流现值",
        "note": "适合长约、特许经营和项目收入。",
    },
    "政府补贴敏感性分析": {
        "type": "敏感性分析",
        "data": "补贴政策、补贴金额、到账周期、取消情景",
        "output": "补贴变化对 IRR/现金流影响",
        "note": "适合政策相关项目。",
    },
    "利用率敏感性分析": {
        "type": "敏感性分析",
        "data": "利用率、上架率、产能爬坡、价格",
        "output": "利用率变化对估值影响",
        "note": "适合数据中心、产线、园区、项目资产。",
    },
    "融资结构敏感性分析": {
        "type": "敏感性分析",
        "data": "债务比例、利率、期限、还本方式",
        "output": "融资结构对权益收益影响",
        "note": "适合带杠杆的项目公司。",
    },
    "资产重估法": {
        "type": "资产估值",
        "data": "账面价值、市场价格、稀缺性、重估假设",
        "output": "重估后资产价值",
        "note": "适合土地、矿权、电力指标、牌照等。",
    },
    "重置成本法": {
        "type": "成本估值",
        "data": "重建成本、折旧、建设周期、替代难度",
        "output": "资产重置价值",
        "note": "适合固定资产和产能类资产。",
    },
    "单位产能估值": {
        "type": "产能估值",
        "data": "单位产能价格、有效产能、利用率",
        "output": "按单位产能估算价值",
        "note": "适合机柜、产线、电站、矿山等。",
    },
    "资源储量估值": {
        "type": "资源估值",
        "data": "储量、品位、开采成本、价格曲线",
        "output": "资源基础价值",
        "note": "适合矿权和资源型资产。",
    },
    "租金/合同现金流估值": {
        "type": "合同估值",
        "data": "租金、合同期限、出租率、续约率",
        "output": "租金或合同现金流现值",
        "note": "适合土地、机柜、物业和长约合同。",
    },
    "折现回收期": {
        "type": "项目收益",
        "data": "折现率、年度现金流、初始投资",
        "output": "动态投资回收期",
        "note": "适合现金流型资产。",
    },
    "可交易资产比较法": {
        "type": "市场比较",
        "data": "可比资产交易价格、权属、期限、流动性",
        "output": "市场比较价值",
        "note": "适合可交易或可转让资产。",
    },
}

MODELS_BY_TYPE = {
    "上市公司": {
        "primary": ["PE", "PB", "PS", "EV/EBITDA", "DCF", "PEG", "SOTP"],
        "auxiliary": ["历史估值分位", "同业比较", "情景估值"],
        "unsuitable": ["流动性折扣", "上市概率折扣", "下轮融资估值推演"],
    },
    "未上市成长公司": {
        "primary": ["可比上市公司法", "可比融资交易法", "收入倍数", "ARR 倍数", "SOTP"],
        "auxiliary": ["用户价值法", "流动性折扣", "上市概率折扣", "二级市场映射法", "情景估值"],
        "unsuitable": ["PB", "历史估值分位", "折现回收期"],
    },
    "一级市场融资标的": {
        "primary": ["可比融资交易法", "可比上市公司法", "融资轮次估值锚", "收入倍数", "利润倍数", "ARR 倍数"],
        "auxiliary": ["订单倍数", "技术成熟度折扣", "流动性折扣", "退出路径折扣", "下轮融资估值推演", "IPO / 并购退出倒推"],
        "unsuitable": ["历史估值分位", "PB"],
    },
    "项目公司 / SPV": {
        "primary": ["DCF", "IRR", "投资回收期", "项目现金流模型"],
        "auxiliary": ["资产价值法", "产能价值法", "合同现金流法", "政府补贴敏感性分析", "利用率敏感性分析", "融资结构敏感性分析"],
        "unsuitable": ["PE", "PEG", "高成长 PS"],
    },
    "资产型项目": {
        "primary": ["资产重估法", "重置成本法", "DCF", "单位产能估值"],
        "auxiliary": ["资源储量估值", "租金/合同现金流估值", "折现回收期", "可交易资产比较法"],
        "unsuitable": ["PE", "PEG", "ARR 倍数"],
    },
}

TYPE_DATA_REQUIREMENTS = {
    "上市公司": [
        "最近三年收入、净利润、毛利率、ROE、经营现金流",
        "当前市值、企业价值、净债务、股本结构",
        "历史 PE/PB/PS/EV/EBITDA 分位",
        "同业公司估值和核心财务指标",
        "分部收入和利润，用于 SOTP",
    ],
    "未上市成长公司": [
        "最近三年收入、ARR、毛利率、客户数量或用户数量",
        "历史融资轮次、投后估值、主要投资方",
        "可比上市公司和可比融资交易样本",
        "退出路径、预计时间、上市或并购概率",
        "股权流动性限制和老股交易条款",
    ],
    "一级市场融资标的": [
        "本轮融资金额、投前估值、投后估值、稀释比例",
        "历史融资轮次和里程碑完成情况",
        "订单、收入、利润或 ARR 的可验证数据",
        "下轮融资关键里程碑和退出路径",
        "技术成熟度、客户验证和量产状态",
    ],
    "项目公司 / SPV": [
        "初始投资额、建设周期、资本开支节奏",
        "产能、利用率、价格、成本、税费和补贴",
        "合同期限、客户信用、回款周期",
        "债务比例、利率、还本付息安排",
        "项目年度现金流、IRR 和回收期假设",
    ],
    "资产型项目": [
        "资产清单、权属、期限、可转让限制",
        "可比资产交易价格或重置成本",
        "资源储量、单位产能、出租率或合同现金流",
        "维护成本、折旧、更新改造投入",
        "资产稀缺性、政策约束和退出方式",
    ],
}


def classify_target(profile: TargetProfile) -> ClassificationResult:
    matched: list[str] = []
    reasons: list[str] = []

    if profile.is_listed:
        matched.append(TARGET_TYPES["listed_company"])
        reasons.append("标的已在公开市场上市交易，优先按上市公司处理。")

    if profile.is_single_project_spv:
        matched.append(TARGET_TYPES["project_spv"])
        reasons.append("标的是单一项目或 SPV，核心问题是项目现金流、回收期和 IRR。")

    if profile.is_asset_or_resource_based:
        matched.append(TARGET_TYPES["asset_project"])
        reasons.append("标的主要依赖资产、资源、牌照、合同或产能，应补充资产价值视角。")

    if not profile.is_listed and profile.is_financing_or_transaction:
        matched.append(TARGET_TYPES["primary_market_deal"])
        reasons.append("标的处于融资、老股转让或一级市场交易场景，应评估本轮定价。")

    if (
        not profile.is_listed
        and profile.is_complete_company
        and not profile.is_single_project_spv
    ):
        matched.append(TARGET_TYPES["private_growth_company"])
        reasons.append("标的是未上市完整公司主体，可作为未上市成长公司建立整体估值框架。")

    matched = dedupe(matched)
    if not matched:
        matched = [TARGET_TYPES["private_growth_company"]]
        reasons.append("信息不足，暂按未上市成长公司建立初步估值框架，后续需补充标的属性。")

    primary = choose_primary_type(matched, profile)
    auxiliary = [item for item in matched if item != primary]
    return ClassificationResult(primary_type=primary, auxiliary_types=auxiliary, reasons=reasons)


def choose_primary_type(matched: list[str], profile: TargetProfile) -> str:
    if TARGET_TYPES["project_spv"] in matched:
        return TARGET_TYPES["project_spv"]
    if TARGET_TYPES["asset_project"] in matched and not profile.is_complete_company:
        return TARGET_TYPES["asset_project"]
    if TARGET_TYPES["listed_company"] in matched:
        return TARGET_TYPES["listed_company"]
    if TARGET_TYPES["primary_market_deal"] in matched:
        return TARGET_TYPES["primary_market_deal"]
    return matched[0]


def recommend_models(profile: TargetProfile, classification: ClassificationResult) -> RecommendationResult:
    type_names = [classification.primary_type] + classification.auxiliary_types
    primary_models = list(MODELS_BY_TYPE[classification.primary_type]["primary"])
    auxiliary_models: list[str] = []
    unsuitable_models: list[str] = list(MODELS_BY_TYPE[classification.primary_type]["unsuitable"])

    for type_name in classification.auxiliary_types:
        auxiliary_models.extend(MODELS_BY_TYPE[type_name]["primary"])
        auxiliary_models.extend(MODELS_BY_TYPE[type_name]["auxiliary"])
        unsuitable_models.extend(MODELS_BY_TYPE[type_name]["unsuitable"])

    auxiliary_models.extend(MODELS_BY_TYPE[classification.primary_type]["auxiliary"])

    if profile.revenue_growth_status == "周期波动" or "船舶" in profile.target_name:
        primary_models = prioritize(primary_models, ["PB", "周期归一化 PE", "EV/EBITDA", "SOTP"])
        auxiliary_models = prioritize(auxiliary_models, ["历史估值分位", "同业比较", "情景估值"])
    if profile.is_profitable and "PE" not in primary_models and classification.primary_type == "上市公司":
        primary_models.append("PE")
    if not profile.has_revenue:
        unsuitable_models.extend(["PE", "PEG", "PS", "收入倍数"])
    if profile.cash_flow_stable and "DCF" not in primary_models:
        auxiliary_models.insert(0, "DCF")

    primary_models = dedupe(primary_models)
    auxiliary_models = [model for model in dedupe(auxiliary_models) if model not in primary_models]
    unsuitable_models = [model for model in dedupe(unsuitable_models) if model not in primary_models and model not in auxiliary_models]

    comparison = build_comparison_table(primary_models, auxiliary_models, unsuitable_models)
    data_requirements = build_data_requirements(type_names)
    rationale = build_rationale(profile, classification)
    return RecommendationResult(
        primary_models=primary_models,
        auxiliary_models=auxiliary_models,
        unsuitable_models=unsuitable_models,
        rationale=rationale,
        comparison_table=comparison,
        data_requirements=data_requirements,
    )


def build_comparison_table(
    primary_models: list[str],
    auxiliary_models: list[str],
    unsuitable_models: list[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for model in primary_models:
        rows.append(model_row(model, "高"))
    for model in auxiliary_models:
        rows.append(model_row(model, "中"))
    for model in unsuitable_models:
        rows.append(model_row(model, "不适用"))
    return rows


def model_row(model: str, applicability: str) -> dict[str, str]:
    meta = MODEL_CATALOG.get(
        model,
        {
            "type": "待定义",
            "data": "待补充",
            "output": "待补充",
            "note": "后续完善。",
        },
    )
    return {
        "模型": model,
        "适用度": applicability,
        "类型": meta["type"],
        "需要的数据": meta["data"],
        "输出结果": meta["output"],
        "备注": meta["note"],
    }


def build_data_requirements(type_names: list[str]) -> list[str]:
    requirements: list[str] = []
    for type_name in type_names:
        requirements.extend(TYPE_DATA_REQUIREMENTS.get(type_name, []))
    return dedupe(requirements)


def build_rationale(profile: TargetProfile, classification: ClassificationResult) -> str:
    if classification.primary_type == "项目公司 / SPV":
        return "该标的核心价值来自项目现金流、建设投入、利用率和融资结构，因此应优先使用 DCF、IRR、投资回收期和项目现金流模型。"
    if classification.primary_type == "资产型项目":
        return "该标的核心价值来自资产、资源、牌照、合同或产能，应优先使用资产重估、重置成本、单位产能和合同现金流方法。"
    if classification.primary_type == "一级市场融资标的":
        return "该标的处于交易定价场景，应重点比较可比融资、可比上市公司、本轮估值锚和退出路径折扣。"
    if classification.primary_type == "未上市成长公司":
        return "该标的是未上市完整公司主体，应结合可比公司、收入/ARR 倍数、可比融资和流动性折扣形成估值框架。"
    if profile.revenue_growth_status == "周期波动":
        return "该上市公司处于周期波动行业，应优先使用 PB、周期归一化 PE、EV/EBITDA、SOTP 和历史估值分位。"
    return "该标的是上市公司，应结合 PE、PB、PS、EV/EBITDA、DCF、PEG、SOTP、历史分位和同业比较建立多模型框架。"


def generate_valuation_memo(
    profile: TargetProfile,
    classification: ClassificationResult,
    recommendation: RecommendationResult,
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    vault = Path(vault_path).expanduser()
    output_dir = vault / "15_估值引擎" / "估值历史"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = safe_filename(profile.target_name)
    output_path = output_dir / f"{safe_name}_{created.isoformat()}_估值框架.md"
    output_path.write_text(
        valuation_memo_markdown(profile, classification, recommendation, created),
        encoding="utf-8",
    )
    return output_path


def valuation_memo_markdown(
    profile: TargetProfile,
    classification: ClassificationResult,
    recommendation: RecommendationResult,
    created: date,
) -> str:
    auxiliary = "、".join(classification.auxiliary_types) if classification.auxiliary_types else "无"
    primary_models = "\n".join(f"- {model}" for model in recommendation.primary_models)
    auxiliary_models = "\n".join(f"- {model}" for model in recommendation.auxiliary_models) or "- 无"
    unsuitable_models = "\n".join(f"- {model}" for model in recommendation.unsuitable_models) or "- 无"
    data_items = "\n".join(f"- {item}" for item in recommendation.data_requirements)
    comparison = markdown_table(recommendation.comparison_table)
    reasons = "\n".join(f"- {reason}" for reason in classification.reasons)
    return f"""---
type: valuation_framework
title: {profile.target_name}估值框架
status: draft
public: false
created: {created.isoformat()}
target_name: {profile.target_name}
target_type: {classification.primary_type}
linked_ecosystem:
  - {profile.ecosystem}
tags:
  - 估值引擎
  - 估值框架
---

# {profile.target_name}估值框架

## 1. 标的基本信息

- 标的名称：{profile.target_name}
- 市场：{profile.market}
- 所属生态：{profile.ecosystem}
- 是否上市：{"是" if profile.is_listed else "否"}
- 是否正在融资或交易：{"是" if profile.is_financing_or_transaction else "否"}
- 是否完整公司主体：{"是" if profile.is_complete_company else "否"}
- 是否单一项目 / SPV：{"是" if profile.is_single_project_spv else "否"}
- 是否主要依赖资产或资源：{"是" if profile.is_asset_or_resource_based else "否"}
- 是否已有收入：{"是" if profile.has_revenue else "否"}
- 是否盈利：{"是" if profile.is_profitable else "否"}
- 收入增长状态：{profile.revenue_growth_status}
- 现金流是否稳定：{"是" if profile.cash_flow_stable else "否"}
- 退出路径：{profile.exit_path}

## 2. 自动识别结果

- 主分类：{classification.primary_type}
- 辅助分类：{auxiliary}

识别依据：

{reasons}

## 3. 推荐估值模型

主模型：

{primary_models}

辅助模型：

{auxiliary_models}

不适用模型：

{unsuitable_models}

原因说明：

{recommendation.rationale}

## 4. 多模型适用性对比

{comparison}

## 5. 需要补充的数据

{data_items}

## 6. 初步估值思路

本阶段先建立估值框架，不输出估值结论。后续需要补充财务、交易、资产、现金流和同业数据，再进行多情景估值测算。

## 7. 风险与不确定性

- 数据真实性和口径一致性。
- 行业周期、政策变化和市场定价波动。
- 技术成熟度、客户验证和商业化进度。
- 退出路径、流动性和融资环境变化。

## 8. 后续研究任务

- 补齐关键财务和经营数据。
- 建立同业和可比交易样本。
- 明确核心估值假设。
- 建立乐观、中性、保守三种情景。
- 将估值框架沉淀为 Rachel Capital OS 内部研究备忘录。

## 9. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def markdown_table(rows: list[dict[str, str]]) -> str:
    columns = ["模型", "适用度", "类型", "需要的数据", "输出结果", "备注"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(escape_table(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def escape_table(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return cleaned or "未命名标的"


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def prioritize(models: list[str], preferred: list[str]) -> list[str]:
    remaining = [model for model in models if model not in preferred]
    return [model for model in preferred if model in models or model in MODEL_CATALOG] + remaining


def analyze_target(profile: TargetProfile) -> tuple[ClassificationResult, RecommendationResult]:
    classification = classify_target(profile)
    recommendation = recommend_models(profile, classification)
    return classification, recommendation

