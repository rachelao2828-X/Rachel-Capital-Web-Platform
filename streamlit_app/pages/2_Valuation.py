import os
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import write_listed_memo, write_private_market_memo
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


def default_vault_path() -> str:
    return os.getenv("OBSIDIAN_VAULT_PATH") or settings.obsidian_vault_path or "/Users/rachelao/Documents/Rachel Capital"


def render_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.write("无")
        return
    for item in items:
        st.write(f"- {item}")


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
