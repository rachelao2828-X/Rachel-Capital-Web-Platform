from datetime import date

import pytest

from app.services.valuation_engine.document_parser import parse_uploaded_document
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import (
    write_listed_memo,
    write_private_market_document_analysis,
    write_private_market_document_valuation_framework,
    write_private_market_memo,
)
from app.services.valuation_engine.private_market import PrivateMarketProfile, analyze_private_market
from app.services.valuation_engine.private_market_extractor import extract_private_market_document


def listed_profile(**overrides) -> ListedCompanyProfile:
    base = {
        "stock_name": "测试公司",
        "ticker": "000000.SZ",
        "market": "A股",
        "industry": "测试行业",
        "ecosystem": "AI基础设施生态",
        "is_profitable": True,
        "revenue_growth_status": "稳定增长",
        "profit_growth_status": "稳定增长",
        "asset_attribute": "轻资产",
        "cash_flow_stability": "一般",
        "is_strong_cycle": False,
        "is_sotp_suitable": False,
        "is_turnaround": False,
    }
    base.update(overrides)
    return ListedCompanyProfile(**base)


def private_profile(**overrides) -> PrivateMarketProfile:
    base = {
        "target_name": "测试标的",
        "initial_type": "不确定，让系统判断",
        "industry": "测试行业",
        "ecosystem": "AI基础设施生态",
        "is_financing_or_transfer": False,
        "is_complete_company": True,
        "is_single_project_spv": False,
        "is_asset_or_contract_based": False,
        "has_revenue": True,
        "is_profitable": False,
        "revenue_growth_status": "高增长",
        "cash_flow_stable": False,
        "exit_path": "IPO",
    }
    base.update(overrides)
    return PrivateMarketProfile(**base)


def models(result) -> set[str]:
    return set(result.primary_models + result.auxiliary_models + result.reference_models)


def test_china_shipbuilding_listed_cycle_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="中国船舶",
            ticker="600150.SH",
            industry="高端制造",
            ecosystem="船舶与国防生态",
            asset_attribute="重资产",
            revenue_growth_status="周期波动",
            profit_growth_status="周期波动",
            is_strong_cycle=True,
            is_sotp_suitable=True,
        )
    )

    assert {"PB", "周期归一化PE", "EV/EBITDA", "SOTP", "历史周期分位"}.issubset(models(result))


def test_hengrui_listed_stable_profit_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="恒瑞医药",
            ticker="600276.SH",
            industry="创新药",
            ecosystem="医疗科技生态",
            is_profitable=True,
            revenue_growth_status="稳定增长",
            profit_growth_status="稳定增长",
            asset_attribute="轻资产",
            cash_flow_stability="稳定",
        )
    )

    assert {"PE", "PEG", "DCF", "EV/EBITDA", "同业比较"}.issubset(models(result))


def test_cambricon_listed_growth_profit_volatility_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="寒武纪",
            ticker="688256.SH",
            industry="AI芯片",
            ecosystem="半导体生态",
            is_profitable=False,
            revenue_growth_status="高增长",
            profit_growth_status="亏损",
            asset_attribute="平台型",
            cash_flow_stability="不稳定",
        )
    )

    assert {"PS", "EV/Sales", "远期 PE", "情景估值", "同业比较"}.issubset(models(result))


def test_openai_secondary_transaction_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="OpenAI 老股交易",
            initial_type="一级市场融资标的",
            is_financing_or_transfer=True,
            is_complete_company=True,
            ecosystem="AI基础设施生态",
            exit_path="IPO",
        )
    )

    assert result.classification.primary_type == "一级市场融资标的"
    assert "未上市成长公司" in result.classification.secondary_types
    assert {"可比融资交易法", "可比上市公司法", "收入倍数", "二级市场映射法", "流动性折扣"}.issubset(models(result))


def test_fluorite_recycling_project_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="氟化钙污泥回收项目",
            initial_type="项目公司 / SPV",
            is_financing_or_transfer=True,
            is_complete_company=False,
            is_single_project_spv=True,
            ecosystem="高端材料生态",
            exit_path="分红回收",
        )
    )

    assert result.classification.primary_type == "项目公司 / SPV"
    assert "一级市场融资标的" in result.classification.secondary_types
    assert {"DCF", "IRR", "投资回收期", "项目现金流模型", "合同现金流法"}.issubset(models(result))


def test_xinyi_green_compute_center_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="信宜绿色算力中心",
            initial_type="项目公司 / SPV",
            is_complete_company=False,
            is_single_project_spv=True,
            is_asset_or_contract_based=True,
            cash_flow_stable=True,
            ecosystem="AI基础设施生态",
            exit_path="分红回收",
        )
    )

    assert result.classification.primary_type == "项目公司 / SPV"
    assert "资产型项目" in result.classification.secondary_types
    assert {"DCF", "IRR", "项目现金流模型", "产能价值法", "利用率敏感性", "融资结构敏感性"}.issubset(models(result))


def test_write_listed_memo_path(tmp_path) -> None:
    profile = listed_profile(stock_name="中国船舶", ticker="600150.SH")
    result = analyze_listed_company(profile)

    output = write_listed_memo(profile, result, tmp_path, created=date(2026, 6, 28))

    assert output == tmp_path / "15_估值引擎" / "估值历史" / "已上市公司" / "中国船舶_2026-06-28_已上市公司估值框架.md"
    content = output.read_text(encoding="utf-8")
    assert "type: listed_company_valuation" in content
    assert "target_type: 已上市公司" in content
    assert "public: false" in content


def test_write_private_market_memo_path(tmp_path) -> None:
    profile = private_profile(target_name="信宜绿色算力中心", is_single_project_spv=True, is_complete_company=False)
    result = analyze_private_market(profile)

    output = write_private_market_memo(profile, result, tmp_path, created=date(2026, 6, 28))

    assert output == tmp_path / "15_估值引擎" / "估值历史" / "未上市一级市场" / "信宜绿色算力中心_2026-06-28_未上市一级市场估值框架.md"
    content = output.read_text(encoding="utf-8")
    assert "type: private_market_valuation" in content
    assert "public: false" in content
    assert "target_type: 项目公司 / SPV" in content


def test_extract_private_market_document_recommends_financing_models() -> None:
    parsed = {
        "file_name": "测试AI公司商业计划书.pdf",
        "file_path": "/tmp/测试AI公司商业计划书.pdf",
        "file_type": "pdf",
        "pages": [{"page_number": 1, "text": "项目名称：测试AI公司\n本轮融资金额：人民币5000万元\n投前估值：人民币5亿元\n核心技术：大模型推理平台\n营业收入：2025年收入3000万元"}],
        "raw_text": "项目名称：测试AI公司\n创始人：张三，前华为AI架构师\n技术负责人：李四\n本轮融资金额：人民币5000万元\n投前估值：人民币5亿元\n核心技术：大模型推理平台\n营业收入：2025年收入3000万元",
        "tables": [],
        "warnings": [],
    }

    extraction = extract_private_market_document(parsed)

    assert extraction["project_basic_info"]["project_name"] == "测试AI公司"
    assert extraction["project_basic_info"]["target_type_guess"] == "一级市场融资标的"
    assert "founder_team" in extraction
    assert "business_model" in extraction
    assert "technology_route" in extraction
    assert "products_and_customers" in extraction
    assert "market_space" in extraction
    assert "capacity_data" in extraction
    assert "cost_structure" in extraction
    assert extraction["founder_team"]["founders"]
    assert "可比融资交易法" in extraction["valuation_readiness"]["recommended_models"]
    assert any(row["来源"] == "文件明确披露" for row in extraction["field_assessments"])
    assert all("是否需要确认" in row for row in extraction["field_assessments"])


def test_write_private_market_document_outputs_public_false(tmp_path) -> None:
    parsed = {
        "file_name": "信宜绿色算力中心BP.pdf",
        "file_path": "/tmp/信宜绿色算力中心BP.pdf",
        "file_type": "pdf",
        "pages": [{"page_number": 1, "text": "项目名称：信宜绿色算力中心\n项目总投资：10亿元\n建设周期：18个月\n产能：规划3000个机柜"}],
        "raw_text": "项目名称：信宜绿色算力中心\n项目总投资：10亿元\n建设周期：18个月\n产能：规划3000个机柜",
        "tables": [],
        "warnings": [],
    }
    extraction = extract_private_market_document(parsed)

    analysis_path = write_private_market_document_analysis(extraction, parsed, tmp_path, created=date(2026, 6, 28))
    framework_path = write_private_market_document_valuation_framework(extraction, parsed, tmp_path, created=date(2026, 6, 28))

    assert analysis_path == tmp_path / "15_估值引擎" / "一级市场项目资料解析" / "信宜绿色算力中心_2026-06-28_项目资料解析.md"
    assert framework_path == tmp_path / "15_估值引擎" / "估值历史" / "未上市一级市场" / "信宜绿色算力中心_2026-06-28_未上市一级市场估值框架.md"
    assert "type: private_market_document_analysis" in analysis_path.read_text(encoding="utf-8")
    assert "public: false" in analysis_path.read_text(encoding="utf-8")
    assert "## 4. 创始团队信息" in analysis_path.read_text(encoding="utf-8")
    assert "## 21. 原始资料关键摘录" in analysis_path.read_text(encoding="utf-8")
    assert "## 10. 创始团队对估值的影响" in framework_path.read_text(encoding="utf-8")
    assert "public: false" in framework_path.read_text(encoding="utf-8")


def test_parse_legacy_ppt_and_doc_warn_without_crashing(tmp_path) -> None:
    ppt = tmp_path / "old_deck.ppt"
    doc = tmp_path / "old_doc.doc"
    ppt.write_bytes(b"legacy ppt")
    doc.write_bytes(b"legacy doc")

    ppt_result = parse_uploaded_document(ppt)
    doc_result = parse_uploaded_document(doc)

    assert ppt_result["file_type"] == "ppt"
    assert ppt_result["extraction_quality"] == "failed"
    assert "PPTX" in " ".join(ppt_result["warnings"])
    assert doc_result["file_type"] == "doc"
    assert doc_result["extraction_quality"] == "failed"
    assert "DOCX" in " ".join(doc_result["warnings"])


def test_parse_docx_extracts_paragraphs_and_tables(tmp_path) -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_heading("项目名称：DOCX测试项目", level=1)
    document.add_paragraph("创始人：王五，连续创业者。融资金额：人民币3000万元。")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "营业收入"
    table.cell(0, 1).text = "2025年5000万元"
    table.cell(1, 0).text = "毛利率"
    table.cell(1, 1).text = "45%"
    path = tmp_path / "docx_test.docx"
    document.save(path)

    result = parse_uploaded_document(path)

    assert result["file_type"] == "docx"
    assert result["extraction_quality"] in {"medium", "high"}
    assert "DOCX测试项目" in result["raw_text"]
    assert result["paragraphs"]
    assert result["tables"]


def test_parse_pptx_extracts_slides_and_tables(tmp_path) -> None:
    pptx = pytest.importorskip("pptx")
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "项目名称：PPTX测试项目"
    slide.placeholders[1].text = "创始团队：赵六，前产业公司高管。本轮融资金额：人民币8000万元。"
    table_shape = slide.shapes.add_table(2, 2, 100000, 2500000, 5000000, 1000000)
    table = table_shape.table
    table.cell(0, 0).text = "收入"
    table.cell(0, 1).text = "1亿元"
    table.cell(1, 0).text = "客户"
    table.cell(1, 1).text = "产业客户"
    path = tmp_path / "pptx_test.pptx"
    presentation.save(path)

    result = parse_uploaded_document(path)

    assert result["file_type"] == "pptx"
    assert result["extraction_quality"] in {"medium", "high"}
    assert "PPTX测试项目" in result["raw_text"]
    assert result["slides"]
    assert result["tables"]
