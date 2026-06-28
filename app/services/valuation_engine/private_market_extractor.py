from __future__ import annotations

import re
from typing import Any

from app.services.valuation_engine.model_registry import dedupe


MISSING = "缺失"
DISCLOSED = "PDF 明确披露"
INFERRED = "系统推断"
CONFIRM = "用户需要确认"


def extract_private_market_document(parsed_document: dict[str, Any]) -> dict[str, Any]:
    text = normalize(parsed_document.get("raw_text", ""))
    project_summary = {
        "project_name": first_match(text, [r"(?:项目名称|项目名)[:：]\s*([^\n]{2,60})"]) or guess_project_name(parsed_document, text),
        "company_name": first_match(text, [r"(?:公司名称|企业名称|主体名称)[:：]\s*([^\n]{2,80})"]),
        "one_sentence_summary": guess_summary(text),
        "industry": guess_industry(text),
        "location": first_match(text, [r"(?:所在地|项目地点|注册地址|建设地点)[:：]\s*([^\n]{2,80})"]),
        "business_model": guess_business_model(text),
        "target_type_guess": guess_target_type(text),
        "rachel_ecosystem_guess": guess_ecosystem(text),
    }
    founder_team_info = {
        "founders": keyword_items(text, ["创始人", "联合创始人", "创始团队"]),
        "management_team": keyword_items(text, ["管理团队", "核心团队", "高管", "CEO", "CTO", "CFO"]),
        "team_background": snippet_after(text, ["团队背景", "创始团队", "核心团队"]),
        "key_person_risk": guess_key_person_risk(text),
    }
    financing_info = {
        "is_fundraising": guess_is_fundraising(text),
        "financing_stage": first_match(text, [r"(?:融资轮次|本轮融资|融资阶段)[:：]\s*([^\n]{2,40})"]),
        "pre_money_valuation": first_match(text, [r"(?:投前估值|Pre-money)[:：]?\s*([^\n，。；;]{2,40})"]),
        "post_money_valuation": first_match(text, [r"(?:投后估值|Post-money)[:：]?\s*([^\n，。；;]{2,40})"]),
        "financing_amount": first_match(text, [r"(?:融资金额|拟融资|募集资金|本轮融资金额)[:：]?\s*([^\n，。；;]{2,40})"]),
        "equity_offered": first_match(text, [r"(?:出让股权|释放股权|股权比例)[:：]?\s*([^\n，。；;]{1,30})"]),
        "previous_round": first_match(text, [r"(?:上一轮|上轮融资|历史融资)[:：]\s*([^\n]{2,80})"]),
    }
    operating_data = {
        "products": keyword_items(text, ["产品", "平台", "系统", "设备", "服务"]),
        "customers": keyword_items(text, ["客户", "合作方", "终端客户", "下游"]),
        "orders_or_contracts": keyword_items(text, ["订单", "合同", "协议", "意向书"]),
        "capacity": first_match(text, [r"(?:产能|设计产能|规划产能)[:：]?\s*([^\n，。；;]{2,60})"]),
        "capacity_utilization": first_match(text, [r"(?:产能利用率|上架率|负荷率|利用率)[:：]?\s*([^\n，。；;]{1,30})"]),
        "construction_period": first_match(text, [r"(?:建设周期|建设期|建设时间)[:：]?\s*([^\n，。；;]{2,40})"]),
        "revenue_model": guess_revenue_model(text),
    }
    financial_data = {
        "historical_revenue": first_match(text, [r"(?:历史收入|营业收入|收入)[:：]?\s*([^\n，。；;]{2,50})"]),
        "forecast_revenue": first_match(text, [r"(?:预计收入|预测收入|未来收入)[:：]?\s*([^\n，。；;]{2,50})"]),
        "gross_margin": first_match(text, [r"(?:毛利率|综合毛利率)[:：]?\s*([0-9.]+%?)"]),
        "net_margin": first_match(text, [r"(?:净利率|净利润率)[:：]?\s*([0-9.]+%?)"]),
        "capex": first_match(text, [r"(?:资本开支|CAPEX|总投资|项目投资)[:：]?\s*([^\n，。；;]{2,50})"]),
        "opex": first_match(text, [r"(?:运营成本|OPEX|期间费用)[:：]?\s*([^\n，。；;]{2,50})"]),
        "cash_flow": first_match(text, [r"(?:现金流|经营性现金流|自由现金流)[:：]?\s*([^\n，。；;]{2,50})"]),
        "payback_period": first_match(text, [r"(?:回收期|投资回收期)[:：]?\s*([^\n，。；;]{2,30})"]),
    }
    cost_structure = {
        "raw_material_cost": first_match(text, [r"(?:原材料成本|材料成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "labor_cost": first_match(text, [r"(?:人工成本|人员成本|薪酬成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "manufacturing_cost": first_match(text, [r"(?:制造成本|生产成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "sales_and_marketing_cost": first_match(text, [r"(?:销售费用|市场费用|获客成本|CAC)[:：]?\s*([^\n，。；;]{2,60})"]),
        "rd_cost": first_match(text, [r"(?:研发费用|研发投入)[:：]?\s*([^\n，。；;]{2,60})"]),
    }
    technology_and_barriers = {
        "core_technology": snippet_after(text, ["核心技术", "技术路线", "自主研发"]),
        "patents": first_match(text, [r"(?:专利|知识产权)[:：]?\s*([^\n]{2,80})"]),
        "technical_maturity": guess_technical_maturity(text),
        "competitive_advantage": snippet_after(text, ["竞争优势", "核心壁垒", "护城河"]),
        "key_dependencies": keyword_items(text, ["供应商", "原材料", "芯片", "设备", "牌照"]),
    }
    market_and_competition = {
        "market_size": first_match(text, [r"(?:市场规模|市场空间|TAM)[:：]?\s*([^\n]{2,80})"]),
        "market_growth": first_match(text, [r"(?:市场增速|复合增长率|CAGR)[:：]?\s*([^\n]{2,60})"]),
        "competitors": keyword_items(text, ["竞争对手", "竞品", "同业"]),
        "comparable_listed_companies": keyword_items(text, ["上市公司", "可比公司"]),
        "comparable_private_companies": keyword_items(text, ["未上市", "创业公司", "独角兽"]),
    }
    risk_factors = {
        "team_risk": guess_team_risk(founder_team_info),
        "key_person_risk": founder_team_info.get("key_person_risk", ""),
        "technology_risk": risk_snippet(text, "技术"),
        "market_risk": risk_snippet(text, "市场"),
        "customer_risk": risk_snippet(text, "客户"),
        "policy_risk": risk_snippet(text, "政策"),
        "financing_risk": risk_snippet(text, "融资"),
        "execution_risk": risk_snippet(text, "执行"),
    }
    exit_path = {
        "ipo_path": snippet_after(text, ["IPO", "上市计划", "上市路径"]),
        "ma_path": snippet_after(text, ["并购退出", "收购退出", "产业并购"]),
        "dividend_or_buyback": snippet_after(text, ["分红", "回购", "股权回购"]),
        "asset_sale": snippet_after(text, ["资产出售", "资产转让"]),
    }
    valuation_readiness = build_valuation_readiness(
        project_summary,
        founder_team_info,
        financing_info,
        operating_data,
        financial_data,
        cost_structure,
        technology_and_barriers,
        market_and_competition,
        risk_factors,
        exit_path,
    )
    extraction = {
        "project_summary": project_summary,
        "founder_team_info": founder_team_info,
        "financing_info": financing_info,
        "operating_data": operating_data,
        "financial_data": financial_data,
        "cost_structure": cost_structure,
        "technology_and_barriers": technology_and_barriers,
        "market_and_competition": market_and_competition,
        "risk_factors": risk_factors,
        "exit_path": exit_path,
        "valuation_readiness": valuation_readiness,
    }
    extraction["field_assessments"] = build_field_assessments(extraction, text)
    extraction["raw_excerpt"] = build_excerpt(text)
    return extraction


def build_valuation_readiness(*sections: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for section in sections:
        merged.update(section)

    target_type = str(merged.get("target_type_guess") or "")
    recommended_models = models_for_target_type(target_type)
    usable_data = []
    missing_data = []
    questions = []
    required_fields = {
        "项目名称": merged.get("project_name"),
        "创始团队": merged.get("founders") or merged.get("management_team") or merged.get("team_background"),
        "行业": merged.get("industry"),
        "商业模式": merged.get("business_model"),
        "融资金额": merged.get("financing_amount"),
        "收入": merged.get("historical_revenue") or merged.get("forecast_revenue"),
        "毛利率": merged.get("gross_margin"),
        "产能": merged.get("capacity"),
        "市场空间": merged.get("market_size"),
        "退出路径": "",
    }
    for label, value in required_fields.items():
        if has_value(value):
            usable_data.append(label)
        else:
            missing_data.append(label)
            questions.append(f"请补充或确认：{label}。")

    confidence_level = "高" if len(missing_data) <= 2 else "中" if len(missing_data) <= 5 else "低"
    if "创始团队" in missing_data and confidence_level == "高":
        confidence_level = "中"
    return {
        "recommended_models": recommended_models,
        "usable_data": usable_data,
        "missing_data": missing_data,
        "questions_for_company": questions,
        "confidence_level": confidence_level,
    }


def models_for_target_type(target_type: str) -> list[str]:
    if target_type == "一级市场融资标的":
        return ["可比融资交易法", "可比上市公司法", "融资轮次估值锚", "收入倍数", "利润倍数", "订单倍数", "IPO / 并购退出倒推", "退出路径折扣"]
    if target_type == "项目公司 / SPV":
        return ["DCF", "IRR", "投资回收期", "项目现金流模型", "合同现金流法", "产能价值法", "利用率敏感性分析", "融资结构敏感性分析"]
    if target_type == "资产型项目":
        return ["资产重估法", "重置成本法", "单位产能估值", "资源储量估值", "合同现金流估值", "可交易资产比较法"]
    return ["可比上市公司法", "可比融资交易法", "收入倍数", "ARR倍数", "二级市场映射法", "流动性折扣", "上市概率折扣"]


def build_field_assessments(extraction: dict[str, Any], text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inferred_fields = {"one_sentence_summary", "target_type_guess", "rachel_ecosystem_guess", "recommended_models", "missing_data", "questions_for_company", "confidence_level"}
    for section_name, section in extraction.items():
        if section_name in {"field_assessments", "raw_excerpt"} or not isinstance(section, dict):
            continue
        for field, value in section.items():
            if isinstance(value, list):
                display = "、".join(str(item) for item in value) if value else ""
            elif value is None:
                display = ""
            else:
                display = str(value)
            if not display:
                source = MISSING
                confidence = "缺失"
                needs_confirmation = True
            elif field in inferred_fields:
                source = INFERRED
                confidence = "中" if field != "confidence_level" else display
                needs_confirmation = True
            elif display and display in text:
                source = DISCLOSED
                confidence = "高"
                needs_confirmation = False
            else:
                source = CONFIRM
                confidence = "低"
                needs_confirmation = True
            rows.append(
                {
                    "分组": section_name,
                    "字段": field,
                    "提取结果": display or "未披露",
                    "来源": source,
                    "可信度": confidence,
                    "是否需要用户确认": "是" if needs_confirmation else "否",
                }
            )
    return rows


def normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text or "").strip()


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean(match.group(1))
    return ""


def guess_project_name(parsed_document: dict[str, Any], text: str) -> str:
    name = PathLikeName(str(parsed_document.get("file_name") or "未命名项目"))
    if name:
        return name
    first_line = next((line.strip() for line in text.splitlines() if len(line.strip()) >= 3), "")
    return clean(first_line[:40]) or "未命名项目"


def PathLikeName(file_name: str) -> str:
    return re.sub(r"[_\-\s]*(项目资料解析|商业计划书|BP|可研报告|\.pdf)$", "", file_name, flags=re.IGNORECASE).strip()[:60]


def guess_summary(text: str) -> str:
    for line in text.splitlines():
        cleaned = clean(line)
        if 12 <= len(cleaned) <= 120 and any(keyword in cleaned for keyword in ["项目", "公司", "平台", "产品", "服务", "建设"]):
            return cleaned
    return clean(text[:100])


def guess_industry(text: str) -> str:
    mapping = [
        ("AI基础设施", ["算力", "AI", "大模型", "数据中心", "GPU"]),
        ("半导体", ["半导体", "芯片", "晶圆", "封装", "设备"]),
        ("机器人", ["机器人", "具身智能", "自动化"]),
        ("高端材料", ["材料", "复合材料", "碳纤维", "陶瓷"]),
        ("医疗科技", ["医疗", "药", "器械", "诊断"]),
        ("新能源 / 绿色资产", ["储能", "光伏", "风电", "绿色", "碳"]),
    ]
    return keyword_mapping(text, mapping, "待确认")


def guess_ecosystem(text: str) -> str:
    mapping = [
        ("AI基础设施生态", ["算力", "AI", "大模型", "数据中心", "GPU"]),
        ("半导体生态", ["半导体", "芯片", "晶圆", "封装"]),
        ("华为生态", ["华为", "鸿蒙", "昇腾", "鲲鹏"]),
        ("机器人生态", ["机器人", "具身智能"]),
        ("高端材料生态", ["材料", "碳纤维", "陶瓷"]),
        ("医疗科技生态", ["医疗", "药", "器械", "诊断"]),
    ]
    return keyword_mapping(text, mapping, "其他")


def guess_target_type(text: str) -> str:
    if any(keyword in text for keyword in ["SPV", "项目公司", "建设期", "项目总投资", "IRR", "回收期"]):
        return "项目公司 / SPV"
    if any(keyword in text for keyword in ["资产", "资源储量", "重置成本", "租金", "长期合同"]):
        return "资产型项目"
    if any(keyword in text for keyword in ["融资", "投前估值", "投后估值", "Pre-IPO", "出让股权", "老股"]):
        return "一级市场融资标的"
    return "未上市成长公司"


def guess_is_fundraising(text: str) -> bool | None:
    if any(keyword in text for keyword in ["拟融资", "本轮融资", "融资金额", "出让股权", "投前估值", "投后估值"]):
        return True
    if any(keyword in text for keyword in ["暂无融资计划", "不融资"]):
        return False
    return None


def guess_business_model(text: str) -> str:
    if "订阅" in text or "SaaS" in text or "ARR" in text:
        return "订阅 / SaaS 收入模式"
    if any(keyword in text for keyword in ["销售", "经销", "订单"]):
        return "产品销售 / 订单交付模式"
    if any(keyword in text for keyword in ["合同", "租赁", "服务费"]):
        return "合同现金流 / 服务费模式"
    return snippet_after(text, ["商业模式", "盈利模式", "收入模式"])


def guess_revenue_model(text: str) -> str:
    return snippet_after(text, ["收入模式", "盈利模式", "收费模式"]) or guess_business_model(text)


def guess_technical_maturity(text: str) -> str:
    if any(keyword in text for keyword in ["量产", "规模化交付", "已投产"]):
        return "已量产 / 已交付，需核验客户与产能数据"
    if any(keyword in text for keyword in ["中试", "试生产", "样机"]):
        return "中试或样机阶段，需核验技术成熟度"
    if any(keyword in text for keyword in ["研发", "实验室", "概念验证"]):
        return "研发阶段，技术成熟度需重点确认"
    return ""


def guess_key_person_risk(text: str) -> str:
    if any(keyword in text for keyword in ["创始人", "核心团队", "CEO", "CTO"]):
        return "已披露部分核心团队信息，需进一步核验股权、履历、稳定性和关键人依赖。"
    return "未充分披露创始团队信息，关键人风险和团队执行力需重点确认。"


def guess_team_risk(founder_team_info: dict[str, Any]) -> str:
    if founder_team_info.get("founders") or founder_team_info.get("management_team") or founder_team_info.get("team_background"):
        return "团队信息已有披露，但仍需核验履历真实性、分工、股权激励和组织稳定性。"
    return "创始团队信息缺失，团队风险较高，估值可用性需下调。"


def keyword_items(text: str, keywords: list[str], limit: int = 5) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        cleaned = clean(line)
        if 6 <= len(cleaned) <= 100 and any(keyword in cleaned for keyword in keywords):
            items.append(cleaned)
        if len(items) >= limit:
            break
    return dedupe(items)


def snippet_after(text: str, keywords: list[str], length: int = 90) -> str:
    for keyword in keywords:
        index = text.find(keyword)
        if index >= 0:
            return clean(text[index : index + length])
    return ""


def risk_snippet(text: str, risk_type: str) -> str:
    for line in text.splitlines():
        cleaned = clean(line)
        if "风险" in cleaned and risk_type in cleaned:
            return cleaned[:100]
    return ""


def keyword_mapping(text: str, mapping: list[tuple[str, list[str]]], fallback: str) -> str:
    for label, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return label
    return fallback


def build_excerpt(text: str) -> str:
    lines = [clean(line) for line in text.splitlines() if len(clean(line)) >= 20]
    return "\n".join(lines[:12])[:1800]


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return bool(value)
    return bool(str(value).strip())


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" -:：\t\r\n")
