import PainCard from "@/components/ui/PainCard";
import ResearchInput from "@/components/home/ResearchInput";
import RoleNavigator from "@/components/home/RoleNavigator";
import CategoryNav from "@/components/home/CategoryNav";
import PainVocabulary from "@/components/home/PainVocabulary";
import ScrollRestoration from "@/components/common/ScrollRestoration";
import { type PainPoint } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchFromAPI<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

const DEMO_PAIN_POINTS: PainPoint[] = [
  {
    id: -1, title: "AI 法律文档自动审查工具",
    summary: "大量中小企业和自由职业者需要审查合同但请不起律师，希望有 AI 工具能自动识别风险条款并给出修改建议。",
    category: "AI", industry: "AI法律", pain_score: 8.2,
    keywords: '["AI", "法律", "合同审查"]', source_urls: null,
    is_saas_idea: true, is_plugin_idea: false,
    business_angle: "面向中小企业的 SaaS 订阅服务", source_count: 12,
    created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    is_individual_feasible: true, feasibility_reason: "核心基于 LLM API，单人可完成",
    estimated_dev_time: "4-8 周", tech_stack_hints: ["Next.js", "OpenAI API", "PostgreSQL"],
    market_saturation: "amber", individual_score: 7.5, opportunity_score: 78,
    demand_validation: null, market_value_analysis: null, implementation_plan: null,
    solo_feasibility: null, snapshot_summary: null, snapshot_opportunity: null,
    snapshot_at: null, enrichment_data: null, enriched_at: null,
  },
  {
    id: -2, title: "跨境电商选品数据分析平台",
    summary: "跨境电商卖家需要从多平台（Amazon、Shopify、TikTok Shop）聚合数据来分析选品趋势，现有工具价格高且数据不全面。",
    category: "电商", industry: "跨境电商", pain_score: 7.8,
    keywords: '["跨境电商", "选品", "数据分析"]', source_urls: null,
    is_saas_idea: true, is_plugin_idea: false,
    business_angle: "按月订阅的数据分析平台", source_count: 8,
    created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    is_individual_feasible: true, feasibility_reason: "爬虫 + 数据处理，独立开发者可完成 MVP",
    estimated_dev_time: "6-10 周", tech_stack_hints: ["Python", "React", "MongoDB"],
    market_saturation: "amber", individual_score: 6.8, opportunity_score: 72,
    demand_validation: null, market_value_analysis: null, implementation_plan: null,
    solo_feasibility: null, snapshot_summary: null, snapshot_opportunity: null,
    snapshot_at: null, enrichment_data: null, enriched_at: null,
  },
  {
    id: -3, title: "独立开发者日志与分析一体化工具",
    summary: "独立开发者需要同时管理多个项目的日志、错误追踪和用户行为分析，现有工具（Sentry、LogRocket）按量计费太贵。",
    category: "DevTools", industry: "独立开发者工具", pain_score: 8.5,
    keywords: '["DevTools", "日志", "监控"]', source_urls: null,
    is_saas_idea: true, is_plugin_idea: true,
    business_angle: "自托管开源 + 云服务双模式", source_count: 15,
    created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    is_individual_feasible: true, feasibility_reason: "开源社区已有类似方案可参考",
    estimated_dev_time: "8-12 周", tech_stack_hints: ["Rust", "React", "ClickHouse"],
    market_saturation: "green", individual_score: 6.0, opportunity_score: 74,
    demand_validation: null, market_value_analysis: null, implementation_plan: null,
    solo_feasibility: null, snapshot_summary: null, snapshot_opportunity: null,
    snapshot_at: null, enrichment_data: null, enriched_at: null,
  },
];

export default async function HomePage() {
  const ppResult = await fetchFromAPI<{ data: PainPoint[]; meta: { total: number } }>(
    "/pain-points?per_page=12&sort_by=opportunity_score"
  );

  const painPoints = ppResult?.data ?? [];
  const total = ppResult?.meta?.total ?? 0;

  const statsResult = total > 0
    ? await fetchFromAPI<{ data: PainPoint[] }>("/pain-points?per_page=1000&sort_by=opportunity_score")
    : null;
  const allPoints = statsResult?.data ?? [];

  const stats = [
    { label: "累计需求", value: String(total), accent: "text-text-primary" },
    { label: "SaaS 机会", value: String(allPoints.filter((p) => p.is_saas_idea).length), accent: "text-amber" },
    { label: "可独立开发", value: String(allPoints.filter((p) => p.is_individual_feasible).length), accent: "text-green" },
  ];

  const isEmpty = painPoints.length === 0;

  return (
    <ScrollRestoration>
      <div className="space-y-8">
        <RoleNavigator />
        <CategoryNav />
        <PainVocabulary />

        <div className="rounded-[10px] border border-hairline bg-surface-1 p-4">
          <p className="text-[12px] text-text-muted mb-2">
            精确搜索：直接输入领域关键词、角色名或痛点描述
          </p>
          <ResearchInput />
        </div>

        {isEmpty ? (
          <div className="rounded-[10px] border border-hairline bg-surface-1 p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-[11px] font-medium text-amber bg-amber-muted px-2 py-0.5 rounded-md">
                示例数据
              </span>
              <span className="text-[12px] text-text-muted">
                以下是真实分析的示例需求。选中上方角色或领域后开始研究，将获取最新数据。
              </span>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {DEMO_PAIN_POINTS.map((pp) => (
                <div
                  key={pp.id}
                  className="rounded-[10px] border border-hairline bg-surface-2 p-5 opacity-70 hover:opacity-100 transition-opacity"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-[14px] font-semibold text-text-primary line-clamp-2">
                      {pp.title}
                    </h3>
                    <span className="shrink-0 font-mono text-lg font-semibold text-amber">
                      {pp.opportunity_score}
                    </span>
                  </div>
                  <p className="mt-2 text-[13px] text-text-secondary line-clamp-3 leading-relaxed">
                    {pp.summary}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {pp.category && (
                      <span className="inline-flex rounded-md bg-surface-3 px-2 py-0.5 text-[11px] text-text-muted">
                        {pp.category}
                      </span>
                    )}
                    {pp.is_individual_feasible && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-green-muted px-2 py-0.5 text-[11px] font-medium text-green">
                        个人可做
                      </span>
                    )}
                    {pp.estimated_dev_time && (
                      <span className="inline-flex items-center rounded-md bg-purple-soft px-2 py-0.5 text-[11px] text-purple-accent">
                        {pp.estimated_dev_time}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-[10px] border border-hairline bg-surface-1 p-5">
                  <p className="text-[12px] text-text-muted">{s.label}</p>
                  <p className={`font-mono text-[28px] font-semibold tracking-tight mt-1 ${s.accent}`}>
                    {s.value}
                  </p>
                </div>
              ))}
            </div>

            <section>
              <h2 className="text-[15px] font-semibold text-text-primary mb-4">需求列表</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {painPoints.map((pp) => (
                  <PainCard key={pp.id} painPoint={pp} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </ScrollRestoration>
  );
}
