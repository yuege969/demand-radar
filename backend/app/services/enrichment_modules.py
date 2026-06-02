from __future__ import annotations

from dataclasses import dataclass, field

PILLAR_DEMAND_VALUE = "demand_value"
PILLAR_EXECUTION_GUIDE = "execution_guide"
PILLAR_COMPETITIVE_INTEL = "competitive_intel"

PILLAR_META: dict[str, dict[str, str]] = {
    PILLAR_DEMAND_VALUE: {
        "key": PILLAR_DEMAND_VALUE,
        "display_name": "值不值得做",
        "description": "判断这个需求是否值得投入",
    },
    PILLAR_EXECUTION_GUIDE: {
        "key": PILLAR_EXECUTION_GUIDE,
        "display_name": "怎么做",
        "description": "落地方案与执行路径",
    },
    PILLAR_COMPETITIVE_INTEL: {
        "key": PILLAR_COMPETITIVE_INTEL,
        "display_name": "竞品分析",
        "description": "市场已有方案与差异化机会",
    },
}


@dataclass
class EnrichmentModule:
    key: str
    pillar: str
    display_name: str
    description: str
    system_prompt: str
    output_fields: list[str] = field(default_factory=list)


ALL_MODULES: list[EnrichmentModule] = [
    # ── Pillar 1: 值不值得做 ──
    EnrichmentModule(
        key="demand_validation",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="需求真伪验证",
        description="判断这是真实痛点还是伪需求",
        output_fields=["is_genuine_demand", "validation_reasoning", "evidence_from_sources",
                       "frequency_analysis", "user_sentiment_intensity"],
        system_prompt="""你是一个市场需求分析专家。请判断下面这个用户痛点是否为真实需求。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "is_genuine_demand": true或false,
  "validation_reasoning": "判断是否为真实需求的详细理由（150-300字），说明判断依据",
  "evidence_from_sources": "从来源内容中提取的具体证据，引用原文关键词句。如果信息不足，请诚实说明",
  "frequency_analysis": "该需求出现的频率判断：偶发吐槽还是普遍痛点，出现场景有哪些",
  "user_sentiment_intensity": "用户情绪分析：紧迫程度、沮丧程度、期望值"
}

如果完全无法判断，返回：{"is_genuine_demand": false, "validation_reasoning": "信息不足，无法判断", "evidence_from_sources": "", "frequency_analysis": "", "user_sentiment_intensity": ""}""",
    ),
    EnrichmentModule(
        key="market_size",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="市场规模估算",
        description="估算潜在用户量级与市场空间",
        output_fields=["total_addressable_users", "market_size_category", "growth_stage",
                       "evidence", "confidence_note"],
        system_prompt="""你是一个市场分析专家。请估算下面这个用户痛点对应的市场规模。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "total_addressable_users": "潜在目标用户总量级估算（如：国内约500万中小学教师），要有具体数字和推导过程",
  "market_size_category": "大市场(>1000万用户)/中等市场(100万-1000万)/小市场(<100万)/极细分(<10万)",
  "growth_stage": "上升期/成熟期/衰退期/新兴领域",
  "evidence": "支撑估算的数据来源或推理依据",
  "confidence_note": "估算的确定性说明，哪些数字是推测的"
}""",
    ),
    EnrichmentModule(
        key="target_user",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="目标用户画像",
        description="谁会为此付费，使用场景是什么",
        output_fields=["primary_users", "secondary_users", "use_scenarios",
                       "decision_chain", "pain_intensity"],
        system_prompt="""你是一个用户研究专家。请为下面这个需求描绘目标用户画像。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "primary_users": "核心用户群体描述：谁最需要这个产品，他们的典型特征是什么",
  "secondary_users": "次要用户群体：还有哪些人可能受益",
  "use_scenarios": ["使用场景1", "使用场景2", "使用场景3"],
  "decision_chain": "付费决策链：谁决定购买、谁使用、谁影响购买决策",
  "pain_intensity": "痛点强度描述：这个问题对用户来说有多痛，不解决会怎样"
}""",
    ),
    EnrichmentModule(
        key="willingness_to_pay",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="付费意愿分析",
        description="用户是否愿意付费，能接受什么价位",
        output_fields=["has_paying_alternatives", "expected_price_range", "willingness_category",
                       "evidence", "pricing_sensitivity"],
        system_prompt="""你是一个商业模式分析专家。请分析下面这个需求的用户付费意愿。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "has_paying_alternatives": "市场上是否已有用户付费的替代方案？举例说明",
  "expected_price_range": "个人开发者产品的合理定价区间（如：9-29元/月 或 一次性买断99-199元），给出具体数字范围",
  "willingness_category": "高付费意愿/中等付费意愿/低付费意愿/免费优先",
  "evidence": "支撑付费意愿判断的依据：用户表达、类似产品定价、行业惯例",
  "pricing_sensitivity": "用户对价格的敏感度分析：是否容易因价格流失"
}""",
    ),

    # ── Pillar 2: 怎么做 ──
    EnrichmentModule(
        key="mvp_definition",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="MVP 产品定义",
        description="第一版产品应该包含哪些核心功能",
        output_fields=["core_features", "scope_boundary", "user_journey",
                       "success_metrics", "mvp_timeline"],
        system_prompt="""你是一个产品设计专家。请为下面这个需求定义MVP（最小可行产品）。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "core_features": ["核心功能1：具体描述", "核心功能2：具体描述", "核心功能3：具体描述"],
  "scope_boundary": "明确不做什么：哪些功能应该推迟到第二版",
  "user_journey": "核心用户旅程：从第一次打开到完成核心任务的关键路径",
  "success_metrics": ["衡量MVP是否成功的关键指标1", "指标2", "指标3"],
  "mvp_timeline": "MVP开发的时间建议：包含设计、开发、测试、内测各阶段"
}""",
    ),
    EnrichmentModule(
        key="tech_approach",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="技术方案推荐",
        description="推荐技术栈与系统架构",
        output_fields=["recommended_stack", "architecture_overview", "key_technical_challenges",
                       "third_party_services", "stack_rationale"],
        system_prompt="""你是一个技术架构师。请为下面这个需求推荐技术方案，面向个人开发者。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "recommended_stack": {
    "frontend": "推荐前端技术及理由（1-2句话）",
    "backend": "推荐后端技术及理由",
    "database": "推荐数据库及理由",
    "hosting": "推荐部署方案及理由"
  },
  "architecture_overview": "系统整体架构简述（100-200字），包括主要模块和数据流",
  "key_technical_challenges": ["技术难点1及建议解决思路", "技术难点2及建议解决思路"],
  "third_party_services": ["可用的第三方服务/API1：用途和优势", "服务2：用途和优势"],
  "stack_rationale": "为什么选择这套技术栈：考虑个人开发者的学习成本、开发效率、运维负担"
}""",
    ),
    EnrichmentModule(
        key="dev_timeline",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="开发周期估算",
        description="各阶段需要多长时间",
        output_fields=["phases", "total_estimate", "parallel_work", "risk_buffer",
                       "assumptions"],
        system_prompt="""你是一个技术项目经理。请为下面这个需求估算个人开发者的开发周期。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "phases": [
    {"phase": "阶段名称", "duration": "预估时长", "tasks": ["关键任务1", "关键任务2"]}
  ],
  "total_estimate": "总计预估时间（如：6-10周，业余时间开发）",
  "parallel_work": "哪些阶段可以并行推进以缩短周期",
  "risk_buffer": "建议预留的缓冲时间及可能延期的风险点",
  "assumptions": "估算的前提假设（如：每周投入20小时、有React基础等）"
}""",
    ),
    EnrichmentModule(
        key="go_to_market",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="推广获客策略",
        description="冷启动方式与获客渠道",
        output_fields=["launch_strategy", "acquisition_channels", "content_strategy",
                       "growth_loops", "initial_metrics"],
        system_prompt="""你是一个增长营销专家。请为下面这个需求设计推广获客策略，面向个人开发者。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "launch_strategy": "冷启动策略：如何在零预算下获取第一批用户",
  "acquisition_channels": [
    {"channel": "渠道名称", "tactics": "具体操作方法", "expected_cost": "预计成本"}
  ],
  "content_strategy": "内容营销策略：可以创作什么内容吸引目标用户",
  "growth_loops": "可能的增长飞轮：用户如何带来更多用户",
  "initial_metrics": ["前3个月应该关注的核心指标1", "指标2", "指标3"]
}""",
    ),
    EnrichmentModule(
        key="monetization_model",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="盈利模式设计",
        description="怎么定价与盈利",
        output_fields=["recommended_model", "pricing_tiers", "revenue_projections",
                       "alternative_models", "key_assumptions"],
        system_prompt="""你是一个商业模式顾问。请为下面这个需求设计盈利模式。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "recommended_model": "推荐的盈利模式（订阅制/买断制/按量付费/免费增值/广告）及理由",
  "pricing_tiers": [
    {"tier": "方案名称", "price": "价格", "features": ["包含功能1", "包含功能2"], "target_user": "目标用户群"}
  ],
  "revenue_projections": "收入预期估算：假设获取100/1000/10000个付费用户时的月收入",
  "alternative_models": ["备选盈利模式1：什么情况下更适合", "备选模式2"],
  "key_assumptions": "盈利模式成立的关键假设"
}""",
    ),

    # ── Pillar 3: 竞品分析 ──
    EnrichmentModule(
        key="competitor_scan",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="现有竞品扫描",
        description="市面上有哪些同类产品",
        output_fields=["direct_competitors", "indirect_competitors", "open_source_alternatives",
                       "market_maturity", "scan_scope"],
        system_prompt="""你是一个竞争情报分析师。请扫描下面这个需求对应的现有产品和解决方案。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "direct_competitors": [
    {"name": "产品名称", "type": "商业产品/开源/个人项目", "brief": "一句话描述", "estimated_users": "粗略用户量级或知名度"}
  ],
  "indirect_competitors": [
    {"name": "产品名称", "type": "间接竞品", "brief": "一句话描述，为什么算间接竞品"}
  ],
  "open_source_alternatives": ["开源替代品1及简要评价", "开源替代品2及简要评价"],
  "market_maturity": "市场成熟度：新兴/成长/成熟/饱和，并说明判断依据",
  "scan_scope": "说明本次扫描的局限性，哪些区域可能遗漏"
}""",
    ),
    EnrichmentModule(
        key="competitor_compare",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="竞品优劣势对比",
        description="竞品做对了什么，做错了什么",
        output_fields=["comparison_table", "common_strengths", "common_weaknesses",
                       "user_complaints", "key_insight"],
        system_prompt="""你是一个产品分析专家。请对比分析下面这个需求领域的竞品优劣势。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "comparison_table": [
    {"product": "产品名", "strengths": ["优势1", "优势2"], "weaknesses": ["劣势1", "劣势2"], "pricing": "价格"}
  ],
  "common_strengths": "竞品普遍做得好的方面",
  "common_weaknesses": "竞品普遍做得差的方面（这是你的机会）",
  "user_complaints": ["来自竞品用户的常见抱怨1", "抱怨2", "抱怨3"],
  "key_insight": "最关键的洞察：看完竞品后最重要的一个结论"
}""",
    ),
    EnrichmentModule(
        key="differentiation",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="差异化切入点",
        description="你的产品可以在哪里做得不一样",
        output_fields=["differentiation_angles", "unique_value_proposition", "blue_ocean_elements",
                       "defensibility", "risks"],
        system_prompt="""你是一个产品战略顾问。请为下面这个需求找出差异化切入点。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "differentiation_angles": [
    {"angle": "差异化方向", "description": "具体如何做到不同", "why_competitors_cant_easily_copy": "为什么竞品不容易复制"}
  ],
  "unique_value_proposition": "一句话独特价值主张：你的产品与其他竞品的本质区别",
  "blue_ocean_elements": "蓝海要素：哪些价值是竞品没有提供但用户需要的",
  "defensibility": "护城河分析：你的差异化是否可持续，还是容易被抄走",
  "risks": ["差异化策略可能失败的风险1", "风险2"]
}""",
    ),
    EnrichmentModule(
        key="market_gap",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="市场空白机会",
        description="有什么需求是竞品还没覆盖的",
        output_fields=["unmet_needs", "underserved_segments", "emerging_opportunities",
                       "adjacent_opportunities", "recommended_entry_point"],
        system_prompt="""你是一个市场机会分析专家。请找出下面这个需求领域的市场空白。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "unmet_needs": [
    {"need": "未满足的需求", "why_unmet": "为什么现有产品没有满足", "opportunity_size": "机会大小评估"}
  ],
  "underserved_segments": [
    {"segment": "被忽视的用户细分", "why_ignored": "为什么被忽视", "potential": "潜力评估"}
  ],
  "emerging_opportunities": ["新兴机会1：由技术趋势或用户行为变化带来的新机会", "新兴机会2"],
  "adjacent_opportunities": ["邻近机会1：可以从这个切入点自然延伸的方向", "邻近机会2"],
  "recommended_entry_point": "建议的市场切入点及理由：从哪里切入最容易被用户接受且竞争最弱"
}""",
    ),
]

_MODULE_MAP: dict[str, EnrichmentModule] | None = None


def get_module_map() -> dict[str, EnrichmentModule]:
    global _MODULE_MAP
    if _MODULE_MAP is None:
        _MODULE_MAP = {m.key: m for m in ALL_MODULES}
    return _MODULE_MAP


def get_module(module_key: str) -> EnrichmentModule | None:
    return get_module_map().get(module_key)


def list_modules() -> list[EnrichmentModule]:
    return list(ALL_MODULES)


def get_pillars() -> list[dict]:
    return [
        {**PILLAR_META[p], "modules": [m for m in ALL_MODULES if m.pillar == p]}
        for p in [PILLAR_DEMAND_VALUE, PILLAR_EXECUTION_GUIDE, PILLAR_COMPETITIVE_INTEL]
    ]
