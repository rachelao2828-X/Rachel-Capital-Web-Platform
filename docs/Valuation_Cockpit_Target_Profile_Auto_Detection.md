# Valuation Cockpit Target Profile Auto Detection

## 1. 为什么保留标的基本信息页

标的基本信息是一级市场估值流程的入口。后续关键假设、估值模型选择、多模型权重、Memo 和项目观察池都依赖这些字段，因此不能删除。

V0.9.1 将该区域升级为“系统自动识别 + 用户确认 / 修正区”，让它成为人机协作的确认门，而不是从零填写的负担。

## 2. 为什么不再要求用户从零手动填写

V0.3-V0.9 已经支持项目资料解析、财务模型读取、关键假设确认、基础估值计算、多模型对比、投资备忘录和项目观察池。

这些模块已经沉淀了项目名称、类型、行业、融资状态、收入、利润、现金流和退出路径等信息。V0.9.1 优先从这些结果中识别基础字段，再交给用户确认。

## 3. 自动识别字段

- 标的名称
- 标的类型
- 所属行业
- 所属 Rachel 战略生态
- 是否正在融资或老股转让
- 是否为完整公司主体
- 是否为单一项目 / SPV
- 是否主要依赖资产、资源、牌照或合同
- 是否已有收入
- 是否盈利
- 收入增长状态
- 现金流是否稳定
- 退出路径

## 4. 字段来源与可信度

每个字段统一保存为：

```json
{
  "detected_value": "",
  "confirmed_value": "",
  "source": "",
  "source_location": "",
  "confidence": "",
  "needs_confirmation": true,
  "notes": ""
}
```

来源包括项目资料解析、Excel / 财务模型、关键假设确认、投资备忘录、项目跟踪记录、文件名、系统推断和用户手动输入。

可信度分为高、中、低、缺失。凡是低可信度、缺失或系统推断字段，都默认需要用户确认。

## 5. 用户确认逻辑

用户点击“自动识别标的基本信息”后，系统生成 `target_profile_draft`。

用户修改确认值后，点击“确认并应用到后续估值流程”，系统写入：

```python
st.session_state["target_profile"]
```

同时同步旧版未上市估值框架所需的基础 widget state，保证旧流程仍可继续使用。

## 6. 与 V0.5-V1.0 的关系

- V0.5 关键假设确认优先读取 `target_profile.confirmed_value`
- V0.6 基础估值计算优先读取确认后的标的名称和类型
- V0.7 多模型估值对比优先读取确认后的标的类型
- V0.8 投资备忘录优先读取确认后的项目名称、行业、生态和标的类型
- V0.9 项目观察池优先读取确认后的项目卡片基础字段
- V1.0 投委会工作流预留接口可继续使用该结构

## 7. JSON 保存路径

确认结果可保存到本地私有目录：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/
```

文件名：

```text
项目名称_YYYY-MM-DD_标的基本信息确认.json
```

该目录不得提交 Git，不得进入 `public_site`。

## 8. Obsidian 输出路径

可生成 Obsidian 标的基本信息确认报告：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/标的基本信息确认/
```

文件名：

```text
项目名称_YYYY-MM-DD_标的基本信息确认.md
```

frontmatter 必须包含：

```yaml
public: false
```

## 9. 隐私与安全边界

- 本功能只用于 localhost 内部研究
- 不发布 GitHub Pages
- 不修改 `public_site`
- 不保存上传文件或解析结果到公开目录
- 不提交 `data/uploads/`
- 不提交 `data/extracted/`
- 不提交 `data/private_market_cases/`
- 所有生成文件默认 `public: false`
- 不生成买卖操作结论、目标价或收益承诺

## 10. 当前限制和下一步计划

当前版本主要基于结构化解析结果、财务字段、历史 JSON 和关键词规则进行识别。扫描版 PDF、非标准 Excel、行业术语缩写和复杂交易结构仍可能需要人工修正。

下一步可以继续增强：

- 引入更细的 source_location 定位
- 对 Excel 多期收入和现金流进行自动 CAGR / 连续正现金流计算
- 增加行业与 Rachel 生态映射词库
- 建立标的类型冲突检测
- 将 V1.0 投委会工作流接入 human review gate
