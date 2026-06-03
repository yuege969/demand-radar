
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Role:
    key: str
    name: str
    icon: str
    description: str
    subtopics: list[str] = field(default_factory=list)


@dataclass
class DomainCategory:
    key: str
    name: str
    description: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class PainWord:
    word: str
    category: str


ROLES: list[Role] = [
    Role(
        key="teacher",
        name="教师",
        icon="📚",
        description="教师群体面临大量重复性行政工作、备课压力和家长沟通负担，是 AI 工具最典型的切入点。",
        subtopics=[
            "备课", "教案", "课件制作", "班主任管理",
            "家校沟通", "表格处理", "行政工作", "作业批改",
        ],
    ),
    Role(
        key="programmer",
        name="程序员",
        icon="💻",
        description="程序员对工具效率极度敏感，付费意愿强，社区活跃，是独立开发者最熟悉的用户群体。",
        subtopics=[
            "Claude Code", "Cursor", "GitHub", "CI/CD",
            "自动化测试", "日志分析", "MCP", "Agent",
            "Docker", "API 开发",
        ],
    ),
    Role(
        key="hr",
        name="HR",
        icon="👥",
        description="HR 日常工作中大量重复筛选、沟通和统计任务，对自动化工具的付费意愿高。",
        subtopics=[
            "简历筛选", "面试安排", "员工统计",
            "考勤管理", "薪酬计算", "入职流程",
        ],
    ),
    Role(
        key="lawyer",
        name="律师",
        icon="⚖️",
        description="律师行业文书工作量大、格式要求高，AI 在合同审查和法律检索方面已有成熟应用。",
        subtopics=[
            "合同审核", "文书生成", "案例检索",
            "法律咨询", "证据整理", "法规追踪",
        ],
    ),
    Role(
        key="cross_border_seller",
        name="跨境卖家",
        icon="🌐",
        description="跨境电商卖家需要同时管理多平台数据，选品、库存、客服等环节痛点多且愿意付费。",
        subtopics=[
            "选品分析", "库存管理", "客服自动化",
            "数据分析", "广告投放", "ERP 集成",
            "多平台管理",
        ],
    ),
    Role(
        key="content_creator",
        name="自媒体创作者",
        icon="📱",
        description="内容生产压力大、多平台分发复杂，创作者对效率工具需求高频且传播力强。",
        subtopics=[
            "小红书运营", "抖音创作", "视频剪辑",
            "选题策划", "数据分析", "私域管理",
            "多平台分发", "B站运营",
        ],
    ),
    Role(
        key="sales",
        name="销售",
        icon="📊",
        description="销售日常工作涉及客户管理、跟进提醒和数据统计，重复性高且直接影响业绩。",
        subtopics=[
            "客户管理", "跟进提醒", "报价生成",
            "销售漏斗", "合同管理", "业绩统计",
        ],
    ),
    Role(
        key="pm",
        name="产品经理",
        icon="🎯",
        description="产品经理需要处理大量需求分析、文档撰写和跨团队沟通，效率工具有明确的付费场景。",
        subtopics=[
            "需求管理", "PRD 撰写", "竞品分析",
            "用户调研", "数据分析", "项目跟踪",
        ],
    ),
]

DOMAIN_CATEGORIES: list[DomainCategory] = [
    DomainCategory(
        key="devtools",
        name="开发者工具",
        description="面向程序员的开发效率、代码质量和运维自动化工具",
        keywords=[
            "Claude Code", "Cursor", "GitHub Copilot", "Trae",
            "MCP", "Agent", "CI/CD", "Docker", "Jenkins",
            "自动化测试", "日志分析", "代码审查", "API 文档",
        ],
    ),
    DomainCategory(
        key="media",
        name="自媒体",
        description="面向内容创作者的选题、制作、分发和数据分析工具",
        keywords=[
            "小红书", "抖音", "视频号", "B站", "公众号",
            "内容创作", "选题", "剪辑", "字幕",
            "封面设计", "多平台分发", "数据分析",
        ],
    ),
    DomainCategory(
        key="education",
        name="教育",
        description="面向教师和教育工作者的备课、教学管理、家校沟通工具",
        keywords=[
            "教师", "备课", "教案", "课件", "班主任",
            "家校沟通", "作业批改", "成绩管理",
            "在线课堂", "题库管理",
        ],
    ),
    DomainCategory(
        key="ecommerce",
        name="电商",
        description="面向电商卖家的选品、运营、库存管理和客服工具",
        keywords=[
            "亚马逊", "Shopee", "TikTok Shop", "淘宝", "拼多多",
            "ERP", "库存管理", "选品", "客服",
            "广告投放", "物流管理", "评价管理",
        ],
    ),
    DomainCategory(
        key="ai_saas",
        name="AI 应用",
        description="基于大模型 API 的垂直场景 AI 应用",
        keywords=[
            "AI", "ChatGPT", "LLM", "大模型", "OpenAI",
            "AI 客服", "AI 写作", "AI 翻译", "AI 搜索",
            "RAG", "智能体", "AI 分析",
        ],
    ),
    DomainCategory(
        key="enterprise",
        name="企业管理",
        description="面向中小企业的管理、协作和流程自动化工具",
        keywords=[
            "HR", "CRM", "OA", "项目管理", "财务管理",
            "报销", "审批", "考勤", "合同管理",
        ],
    ),
]

PAIN_VOCABULARY: list[PainWord] = [
    # 情绪表达
    PainWord(word="烦死了", category="情绪表达"),
    PainWord(word="太麻烦了", category="情绪表达"),
    PainWord(word="崩溃", category="情绪表达"),
    PainWord(word="受不了", category="情绪表达"),
    PainWord(word="累死了", category="情绪表达"),
    PainWord(word="头疼", category="情绪表达"),
    # 求推荐
    PainWord(word="有没有工具", category="求推荐"),
    PainWord(word="有没有软件", category="求推荐"),
    PainWord(word="求推荐", category="求推荐"),
    PainWord(word="有没有办法", category="求推荐"),
    PainWord(word="推荐一下", category="求推荐"),
    PainWord(word="有推荐的吗", category="求推荐"),
    # 效率低
    PainWord(word="效率太低", category="效率低"),
    PainWord(word="浪费时间", category="效率低"),
    PainWord(word="每天都要做", category="重复劳动"),
    PainWord(word="重复劳动", category="重复劳动"),
    PainWord(word="手动操作", category="重复劳动"),
    PainWord(word="总是出错", category="重复劳动"),
    # 不会/找不到
    PainWord(word="不会做", category="能力不足"),
    PainWord(word="找不到", category="能力不足"),
    PainWord(word="经常忘记", category="能力不足"),
    PainWord(word="不知道怎么做", category="能力不足"),
    # 付费
    PainWord(word="愿意付费", category="付费意愿"),
    PainWord(word="有付费的吗", category="付费意愿"),
    PainWord(word="免费试用", category="付费意愿"),
]

_VOCABULARY_BY_CATEGORY: dict[str, list[str]] | None = None


def get_vocabulary_by_category() -> dict[str, list[str]]:
    global _VOCABULARY_BY_CATEGORY
    if _VOCABULARY_BY_CATEGORY is None:
        result: dict[str, list[str]] = {}
        for pw in PAIN_VOCABULARY:
            result.setdefault(pw.category, []).append(pw.word)
        _VOCABULARY_BY_CATEGORY = result
    return _VOCABULARY_BY_CATEGORY


def get_role_by_key(key: str) -> Role | None:
    for r in ROLES:
        if r.key == key:
            return r
    return None
