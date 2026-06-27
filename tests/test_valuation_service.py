from datetime import date

from app.services.valuation_service import TargetProfile, analyze_target, generate_valuation_memo


def profile(**overrides) -> TargetProfile:
    base = {
        "target_name": "测试标的",
        "is_listed": False,
        "market": "未上市",
        "is_financing_or_transaction": False,
        "is_complete_company": True,
        "is_single_project_spv": False,
        "is_asset_or_resource_based": False,
        "has_revenue": True,
        "is_profitable": False,
        "revenue_growth_status": "高增长",
        "cash_flow_stable": False,
        "ecosystem": "AI基础设施生态",
        "exit_path": "IPO",
    }
    base.update(overrides)
    return TargetProfile(**base)


def model_names(result) -> set[str]:
    return set(result.primary_models + result.auxiliary_models)


def test_china_shipbuilding_is_listed_company_with_cycle_models() -> None:
    target = profile(
        target_name="中国船舶",
        is_listed=True,
        market="A股",
        is_complete_company=True,
        is_profitable=True,
        revenue_growth_status="周期波动",
        ecosystem="船舶与国防生态",
    )

    classification, recommendation = analyze_target(target)

    assert classification.primary_type == "上市公司"
    assert {"PB", "周期归一化 PE", "EV/EBITDA", "SOTP"}.issubset(model_names(recommendation))


def test_openai_secondary_transaction_is_primary_market_with_growth_auxiliary() -> None:
    target = profile(
        target_name="OpenAI 老股交易",
        is_financing_or_transaction=True,
        is_complete_company=True,
        has_revenue=True,
        is_profitable=False,
        ecosystem="AI基础设施生态",
        exit_path="IPO",
    )

    classification, recommendation = analyze_target(target)

    assert classification.primary_type == "一级市场融资标的"
    assert "未上市成长公司" in classification.auxiliary_types
    assert {"可比上市公司法", "收入倍数", "可比融资交易法", "流动性折扣"}.issubset(
        model_names(recommendation)
    )


def test_fluorite_sludge_recycling_project_is_project_spv() -> None:
    target = profile(
        target_name="氟化钙污泥回收项目",
        market="项目型",
        is_financing_or_transaction=True,
        is_complete_company=False,
        is_single_project_spv=True,
        is_asset_or_resource_based=False,
        revenue_growth_status="稳定增长",
        cash_flow_stable=True,
        ecosystem="高端材料生态",
        exit_path="分红回收",
    )

    classification, recommendation = analyze_target(target)

    assert classification.primary_type == "项目公司 / SPV"
    assert "一级市场融资标的" in classification.auxiliary_types
    assert {"DCF", "IRR", "投资回收期", "项目现金流模型"}.issubset(model_names(recommendation))


def test_xinyi_green_compute_center_is_project_and_asset() -> None:
    target = profile(
        target_name="信宜绿色算力中心",
        market="项目型",
        is_complete_company=False,
        is_single_project_spv=True,
        is_asset_or_resource_based=True,
        revenue_growth_status="稳定增长",
        cash_flow_stable=True,
        ecosystem="AI基础设施生态",
        exit_path="分红回收",
    )

    classification, recommendation = analyze_target(target)

    assert classification.primary_type == "项目公司 / SPV"
    assert "资产型项目" in classification.auxiliary_types
    assert {"项目现金流模型", "IRR", "资产价值法", "利用率敏感性分析"}.issubset(
        model_names(recommendation)
    )


def test_generate_obsidian_valuation_memo(tmp_path) -> None:
    target = profile(
        target_name="信宜绿色算力中心",
        market="项目型",
        is_complete_company=False,
        is_single_project_spv=True,
        is_asset_or_resource_based=True,
        cash_flow_stable=True,
        ecosystem="AI基础设施生态",
    )
    classification, recommendation = analyze_target(target)

    output_path = generate_valuation_memo(
        profile=target,
        classification=classification,
        recommendation=recommendation,
        vault_path=tmp_path,
        created=date(2026, 6, 27),
    )

    assert output_path == tmp_path / "15_估值引擎" / "估值历史" / "信宜绿色算力中心_2026-06-27_估值框架.md"
    content = output_path.read_text(encoding="utf-8")
    assert "type: valuation_framework" in content
    assert "public: false" in content
    assert "target_type: 项目公司 / SPV" in content
    assert "本文件仅用于 Rachel Capital OS 内部研究" in content
