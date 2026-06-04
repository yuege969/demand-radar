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


# ── 通用质量要求 ──
_QUALITY_RULES = """

【核心原则】
- 宁可少写，不写废话。每个字都要有价值。
- 给出的必须是 "可执行的洞察"，而不是 "正确的废话"。
- 如果缺乏信息，坦诚说明局限性，不要编造或过度推测。
- 面向个人开发者/小团队，建议必须接地气、可落地。

【禁止行为】
- 禁止泛泛而谈的套话，如 "该需求具有一定的市场潜力"
- 禁止放之四海而皆准的建议，如 "关注用户体验"
- 禁止罗列教科书式的知识
- 禁止过度乐观或不切实际的估算

【输出格式】
整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。
"""

ALL_MODULES: list[EnrichmentModule] = [
    # ═══════════════════════════════════════════
    # Pillar 1: 值不值得做
    # ═══════════════════════════════════════════
    EnrichmentModule(
        key="demand_validation",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="需求真伪验证",
        description="判断这是真实痛点还是伪需求",
        output_fields=["is_genuine_demand", "validation_reasoning", "evidence_from_sources",
                       "frequency_analysis", "user_sentiment_intensity"],
        system_prompt="""你是产品判断专家。一句话判断：这个需求值不值得做。

""" + _QUALITY_RULES + """

{
  "is_genuine_demand": true或false,
  "validation_reasoning": "最关键的判断依据，50字以内，不要长篇大论",
  "evidence_from_sources": "从来源中提取的2-3个关键词或原句，证明用户真实表达了该需求。信息不足就说'来源信息有限'",
  "frequency_analysis": "是'天天有人喊'还是'偶尔有人提'？给出判断依据",
  "user_sentiment_intensity": "用户表达该需求时的情绪——愤怒、焦虑、无奈、还是随口一提？1-2个词精确概括"
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
        system_prompt="""你是市场分析师。用最诚实的方式回答：这个市场有多大。

""" + _QUALITY_RULES + """

{
  "total_addressable_users": "给出具体数字区间（如：国内200-500万），说明推导过程。必须可验证",
  "market_size_category": "大市场(>1000万)/中等(100万-1000万)/小众(<100万)/极细分(<10万)",
  "growth_stage": "上升期/成熟期/衰退期/新兴——一句话解释为什么",
  "evidence": "支撑数据，没有就说没有",
  "confidence_note": "诚实标注可信度。纯属猜测就直说'数据不足，无法可靠估算'"
}""",
    ),
    EnrichmentModule(
        key="target_user",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="目标用户画像",
        description="谁会为此付费，使用场景是什么",
        output_fields=["primary_users", "secondary_users", "use_scenarios",
                       "decision_chain", "pain_intensity"],
        system_prompt="""你是用户研究员。精准刻画那个会为这个产品付费的人。

""" + _QUALITY_RULES + """

{
  "primary_users": "用一个具体的典型人物描述核心用户（如：'25-35岁远程办公者，每天开30+标签页的Chrome重度用户'），不要写'有XX需求的人群'",
  "secondary_users": "次要用户。没有明显次要用户就写'无'",
  "use_scenarios": ["具体触发场景1", "具体触发场景2"],
  "decision_chain": "谁决定买、谁用、谁影响？简化回答",
  "pain_intensity": "用户现在怎么将就？将就的代价多高？用具体行为描述，不要形容词堆砌"
}""",
    ),
    EnrichmentModule(
        key="willingness_to_pay",
        pillar=PILLAR_DEMAND_VALUE,
        display_name="付费意愿分析",
        description="用户是否愿意付费，能接受什么价位",
        output_fields=["has_paying_alternatives", "expected_price_range", "willingness_category",
                       "evidence", "pricing_sensitivity"],
        system_prompt="""你是商业化分析师。核心问题：用户会为这个掏钱吗？

""" + _QUALITY_RULES + """

{
  "has_paying_alternatives": "列出1-3个用户已在付费的替代方案（产品名+价格）。找不到就说'未发现明确付费替代'",
  "expected_price_range": "具体价格数字（如：月付19-39元，或买断99-199元），解释定价逻辑",
  "willingness_category": "高付费意愿/中等/低/免费优先——一句话解释",
  "evidence": "支撑判断的1-2个具体依据",
  "pricing_sensitivity": "一句话：用户对价格敏感吗？便宜了怀疑质量，贵了直接走人？"
}""",
    ),

    # ═══════════════════════════════════════════
    # Pillar 2: 怎么做
    # ═══════════════════════════════════════════
    EnrichmentModule(
        key="mvp_definition",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="MVP 产品定义",
        description="第一版产品应该包含哪些核心功能",
        output_fields=["core_features", "scope_boundary", "user_journey",
                       "success_metrics", "mvp_timeline"],
        system_prompt="""你是产品设计专家。定义那个可以两周内上线的极致MVP。

""" + _QUALITY_RULES + """

{
  "core_features": ["核心功能1：15字以内描述，一看就懂", "核心功能2：同上", "核心功能3：同上", "核心功能4：同上"],
  "scope_boundary": "一句话：V1绝对不做什么。只列真正会造成诱惑的功能",
  "user_journey": "用户从打开到获得价值的路径，3-5步（如：'打开插件→点击休眠→内存从2GB降到200MB→产生aha moment'）",
  "success_metrics": ["可量化指标（如'7天留存率>30%'），不要'用户满意度'这种"],
  "mvp_timeline": "原型→开发→内测→上线，每阶段给具体周数"
}""",
    ),
    EnrichmentModule(
        key="tech_approach",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="技术方案推荐",
        description="推荐技术栈与系统架构",
        output_fields=["recommended_stack", "architecture_overview", "key_technical_challenges",
                       "third_party_services", "stack_rationale"],
        system_prompt="""你是技术架构师。给个人开发者推荐最务实的技术方案。

""" + _QUALITY_RULES + """

{
  "recommended_stack": {
    "frontend": "具体框架+关键库，一句话说为什么",
    "backend": "具体框架+关键库，不需要就说'无需后端'",
    "database": "具体数据库，用BaaS就说BaaS自带",
    "hosting": "具体部署方案，优先考虑免费方案（如：Vercel免费版+Supabase免费版）"
  },
  "architecture_overview": "最简短架构描述（100字以内），只说关键2-3个模块",
  "key_technical_challenges": ["真正的技术难点及解决思路", "没有就说'无明显技术难点'"],
  "third_party_services": ["具体可用的第三方API/服务，没有写'无'"],
  "stack_rationale": "一句话：为什么选这套——突出便宜、快、好维护"
}""",
    ),
    EnrichmentModule(
        key="dev_timeline",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="开发周期估算",
        description="各阶段需要多长时间",
        output_fields=["phases", "total_estimate", "parallel_work", "risk_buffer",
                       "assumptions"],
        system_prompt="""你是技术PM。给个人开发者一个诚实不注水的工期估算。

""" + _QUALITY_RULES + """

{
  "phases": [
    {"phase": "阶段名", "duration": "X周（注明全职业余）", "tasks": ["最关键任务3-5个"]}
  ],
  "total_estimate": "总计（注明全职业余，如：'业余8-12周' 或 '全职3-4周'）",
  "parallel_work": "哪些可以并行？一句话",
  "risk_buffer": "最大延期风险是什么？建议留多少缓冲？",
  "assumptions": "估算前提（如：'有React基础，每天投入3小时'），必须诚实"
}""",
    ),
    EnrichmentModule(
        key="go_to_market",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="推广获客策略",
        description="冷启动方式与获客渠道",
        output_fields=["launch_strategy", "acquisition_channels", "content_strategy",
                       "growth_loops", "initial_metrics"],
        system_prompt="""你是增长黑客。帮个人开发者用0预算获取第一批用户。

""" + _QUALITY_RULES + """

{
  "launch_strategy": "最有效的1-2个冷启动方法，具体到在哪个平台发什么内容（如：'在V2EX分享创造节点发帖，标题用XXX'），不要'利用社交媒体推广'这种废话",
  "acquisition_channels": [
    {"channel": "具体渠道（Product Hunt/即刻/小红书等）", "tactics": "在该渠道的具体操作步骤", "expected_cost": "预计花费（0元写0元）"}
  ],
  "content_strategy": "1-2个具体内容选题，不要'写博客'这种泛泛建议",
  "growth_loops": "存在病毒/口碑传播就具体描述，没有就说'主要依赖主动推广'",
  "initial_metrics": ["上线第一个月死盯的1-3个可量化指标"]
}""",
    ),
    EnrichmentModule(
        key="monetization_model",
        pillar=PILLAR_EXECUTION_GUIDE,
        display_name="盈利模式设计",
        description="怎么定价与盈利",
        output_fields=["recommended_model", "pricing_tiers", "revenue_projections",
                       "alternative_models", "key_assumptions"],
        system_prompt="""你是商业化顾问。设计最简单最可能跑通的收费方式。

""" + _QUALITY_RULES + """

{
  "recommended_model": "选一种（订阅/买断/按量/免费增值），一句话解释为什么适合",
  "pricing_tiers": [
    {"tier": "方案名", "price": "具体价格", "features": ["核心差异功能2-4个"], "target_user": "谁会选这个方案"}
  ],
  "revenue_projections": "诚实估算：100个付费用户月入多少？1000个呢？不画大饼",
  "alternative_models": "备选方案，一句话",
  "key_assumptions": "盈利模式成立需要什么条件？"
}""",
    ),

    # ═══════════════════════════════════════════
    # Pillar 3: 竞品分析
    # ═══════════════════════════════════════════
    EnrichmentModule(
        key="competitor_scan",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="现有竞品扫描",
        description="市面上有哪些同类产品",
        output_fields=["direct_competitors", "indirect_competitors", "open_source_alternatives",
                       "market_maturity", "scan_scope"],
        system_prompt="""你是竞争情报分析师。诚实列出已知竞品，不知道就说不知道。

""" + _QUALITY_RULES + """

{
  "direct_competitors": [
    {"name": "产品名", "type": "商业/开源/个人项目", "brief": "一句话核心卖点（15字以内）", "estimated_users": "百万级/十万级/千级/小众/未知"}
  ],
  "indirect_competitors": [
    {"name": "产品名", "type": "间接竞品", "brief": "为什么算竞品"}
  ],
  "open_source_alternatives": ["产品名+一句话评价"],
  "market_maturity": "新兴/成长/成熟/饱和——一句话解释",
  "scan_scope": "诚实说明局限性。基于训练数据而非实时搜索的，请明确说明"
}""",
    ),
    EnrichmentModule(
        key="competitor_compare",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="竞品优劣势对比",
        description="竞品做对了什么，做错了什么",
        output_fields=["comparison_table", "common_strengths", "common_weaknesses",
                       "user_complaints", "key_insight"],
        system_prompt="""你是产品分析专家。找出竞品最致命的短板——那才是你的机会。

""" + _QUALITY_RULES + """

{
  "comparison_table": [
    {"product": "产品名", "strengths": ["最大优势1-2个"], "weaknesses": ["最致命劣势1-2个"], "pricing": "价格"}
  ],
  "common_strengths": "一句话：竞品共同做对的事",
  "common_weaknesses": "一句话：竞品共同的问题——这是你的突破口",
  "user_complaints": ["竞品用户最真实的抱怨，要具体场景（不要泛泛的'不好用'）"],
  "key_insight": "看完竞品后最重要的结论——一句话说清你能赢在哪（30字以内）。这是整个分析最有价值的部分"
}""",
    ),
    EnrichmentModule(
        key="differentiation",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="差异化切入点",
        description="你的产品可以在哪里做得不一样",
        output_fields=["differentiation_angles", "unique_value_proposition", "blue_ocean_elements",
                       "defensibility", "risks"],
        system_prompt="""你是产品战略顾问。找到一个尖刀般的差异化切入点，而非不痛不痒的微创新。

""" + _QUALITY_RULES + """

{
  "differentiation_angles": [
    {"angle": "差异化方向（要尖锐，如：'不是更好的标签管理，而是让用户忘记标签管理'）", "description": "具体怎么做（50字以内）", "why_competitors_cant_easily_copy": "为什么竞品不容易抄？必须有实质壁垒（技术/数据/网络效应），不要'体验更好'这种"}
  ],
  "unique_value_proposition": "一句话，让目标用户一听就想试试（如：'一键休眠，释放95%内存'），不要'专业的XX解决方案'",
  "blue_ocean_elements": "竞品完全没做但用户真正需要的东西。找不到就说'当前差异化空间有限'",
  "defensibility": "一句话：优势能保持多久？会被大厂一个版本迭代覆盖吗？",
  "risks": ["最大具体风险，不要'竞争激烈'这种废话"]
}""",
    ),
    EnrichmentModule(
        key="market_gap",
        pillar=PILLAR_COMPETITIVE_INTEL,
        display_name="市场空白机会",
        description="有什么需求是竞品还没覆盖的",
        output_fields=["unmet_needs", "underserved_segments", "emerging_opportunities",
                       "adjacent_opportunities", "recommended_entry_point"],
        system_prompt="""你是市场机会分析师。找到那个被所有人忽视但真实存在的机会。

""" + _QUALITY_RULES + """

{
  "unmet_needs": [
    {"need": "未被满足的具体需求（不是'更好的体验'这种）", "why_unmet": "为什么没人做？技术难/商业价值低/没发现？", "opportunity_size": "能撬动多大用户群？"}
  ],
  "underserved_segments": [
    {"segment": "被忽视的具体群体（如：'非技术背景小团队'）", "why_ignored": "为什么被忽视？", "potential": "商业潜力"}
  ],
  "emerging_opportunities": ["新技术或行为变化带来的机会，没有写'暂无'"],
  "adjacent_opportunities": ["可自然延伸的邻近机会1-2个"],
  "recommended_entry_point": "一句话：最推荐的切入角度，具体到产品形态（如：'Chrome插件，从标签页休眠单点切入'）"
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
