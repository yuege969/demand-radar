"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getPainPoint,
  getEnrichmentModules,
  enrichPainPoint,
  type PainPointDetail,
  type EnrichmentPillar,
  type EnrichmentModuleInfo,
  type DemandValidation,
  type MarketValueAnalysis,
  type ImplementationPlan,
  type SoloFeasibility,
} from "@/lib/api";
import { formatDate, formatScore, scoreColor, toDisplayScore } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

function parseAnalysis<T>(jsonStr: string | null): T | null {
  if (!jsonStr) return null;
  try {
    return JSON.parse(jsonStr) as T;
  } catch {
    return null;
  }
}

function AnalysisField({ label, text }: { label: string; text: string }) {
  if (!text) return null;
  return (
    <div className="mb-4 last:mb-0">
      <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
      <p className="text-sm text-gray-800 leading-relaxed">{text}</p>
    </div>
  );
}

function ModuleCheckbox({
  module,
  checked,
  onChange,
  isEnriching,
}: {
  module: EnrichmentModuleInfo;
  checked: boolean;
  onChange: (key: string, checked: boolean) => void;
  isEnriching: boolean;
}) {
  const disabled = module.completed;
  return (
    <label
      className={`flex items-start gap-2 rounded-lg border p-3 transition-colors ${
        module.completed
          ? "border-green-200 bg-green-50 cursor-default"
          : "border-gray-200 bg-white cursor-pointer hover:border-indigo-300 hover:bg-indigo-50"
      }`}
    >
      <input
        type="checkbox"
        checked={checked || module.completed}
        disabled={disabled || isEnriching}
        onChange={(e) => onChange(module.key, e.target.checked)}
        className="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{module.display_name}</span>
          {module.completed && (
            <span className="inline-flex items-center rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">
              已完成
            </span>
          )}
          {isEnriching && checked && !module.completed && (
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-1.5 py-0.5 text-xs font-medium text-indigo-600">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
              分析中
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5">{module.description}</p>
      </div>
    </label>
  );
}

export default function PainPointDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [data, setData] = useState<PainPointDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [pillars, setPillars] = useState<EnrichmentPillar[]>([]);
  const [selectedModules, setSelectedModules] = useState<Set<string>>(new Set());
  const [isEnriching, setIsEnriching] = useState(false);

  const loadData = useCallback(async () => {
    if (!id) return;
    const res = await getPainPoint(id);
    if (res.success && res.data) setData(res.data);
    setLoading(false);
  }, [id]);

  const loadModules = useCallback(async () => {
    if (!id) return;
    const res = await getEnrichmentModules(id);
    if (res.success && res.data) setPillars(res.data);
  }, [id]);

  useEffect(() => {
    loadData();
    loadModules();
  }, [loadData, loadModules]);

  // Poll while enriching
  useEffect(() => {
    if (!isEnriching) return;
    const interval = setInterval(() => {
      loadData();
      loadModules();
    }, 2000);
    return () => clearInterval(interval);
  }, [isEnriching, loadData, loadModules]);

  function toggleModule(key: string, checked: boolean) {
    setSelectedModules((prev) => {
      const next = new Set(prev);
      if (checked) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  async function handleEnrich() {
    if (selectedModules.size === 0) return;
    const pending: string[] = [];
    for (const p of pillars) {
      for (const m of p.modules) {
        if (selectedModules.has(m.key) && !m.completed) {
          pending.push(m.key);
        }
      }
    }
    if (pending.length === 0) return;

    setIsEnriching(true);
    await enrichPainPoint(id, pending);
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-2/3 rounded bg-gray-200" />
        <div className="h-4 w-full rounded bg-gray-100" />
        <div className="h-48 rounded-xl bg-gray-100" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20">
        <p className="text-lg text-gray-500">需求未找到</p>
        <Link href="/" className="text-indigo-600 hover:underline mt-2 inline-block">
          返回首页
        </Link>
      </div>
    );
  }

  const breakdown = data.score_breakdown;
  const dimensions = breakdown
    ? [
        { key: "emotion_intensity", label: "情绪强度", w: 0.2 },
        { key: "comment_volume", label: "讨论热度", w: 0.15 },
        { key: "repeat_frequency", label: "重复频率", w: 0.2 },
        { key: "involves_money", label: "付费意愿", w: 0.2 },
        { key: "has_paid_solution", label: "已有方案", w: 0.1 },
        { key: "automation_difficulty", label: "实现难度", w: 0.1 },
        { key: "is_long_term", label: "长期需求", w: 0.05 },
      ]
    : [];

  // Legacy enriched content (backward compat)
  const demandValidation = parseAnalysis<DemandValidation>(data.demand_validation);
  const marketValue = parseAnalysis<MarketValueAnalysis>(data.market_value_analysis);
  const implementation = parseAnalysis<ImplementationPlan>(data.implementation_plan);
  const soloFeasibility = parseAnalysis<SoloFeasibility>(data.solo_feasibility);

  // New enrichment data
  const enrichmentData = parseAnalysis<Record<string, { completed_at: string; result: unknown }>>(
    data.enrichment_data
  );

  const pendingCount = [...selectedModules].filter((k) => {
    for (const p of pillars) {
      for (const m of p.modules) {
        if (m.key === k && !m.completed) return true;
      }
    }
    return false;
  }).length;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <Link href="/" className="text-sm text-gray-500 hover:text-indigo-600">
        &larr; 返回列表
      </Link>

      {/* Header */}
      <header className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
          <div className="shrink-0 text-right">
            <span
              className={`text-3xl font-bold ${scoreColor(toDisplayScore(data.opportunity_score, data.pain_score))}`}
            >
              {formatScore(toDisplayScore(data.opportunity_score, data.pain_score))}
            </span>
            {data.opportunity_score > 0 && <p className="text-xs text-gray-400 mt-0.5">机会分</p>}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.is_individual_feasible ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
              个人可做
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
              门槛较高
            </span>
          )}
          {data.market_saturation && (
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                data.market_saturation === "green"
                  ? "bg-blue-100 text-blue-700"
                  : data.market_saturation === "amber"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-red-100 text-red-700"
              }`}
            >
              {data.market_saturation === "green" ? "蓝海" : data.market_saturation === "amber" ? "中等" : "红海"}
            </span>
          )}
          {data.category && <Badge label={data.category} variant="category" />}
          {data.industry && <Badge label={data.industry} variant="industry" />}
        </div>
      </header>

      {/* Snapshot Section */}
      {(data.snapshot_summary || data.snapshot_opportunity) && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <h2 className="font-semibold text-amber-900">AI 快照分析</h2>
            {data.snapshot_at && (
              <span className="text-xs text-amber-500 ml-auto">{formatDate(data.snapshot_at)}</span>
            )}
          </div>
          {data.snapshot_summary && (
            <p className="text-amber-900 leading-relaxed mb-3">{data.snapshot_summary}</p>
          )}
          {data.snapshot_opportunity && (
            <div className="rounded-lg bg-white border border-amber-200 p-4">
              <p className="text-xs font-medium text-amber-700 mb-1">产品机会</p>
              <p className="text-sm text-amber-800 leading-relaxed">{data.snapshot_opportunity}</p>
            </div>
          )}
        </section>
      )}

      {/* Fallback: show raw summary if no snapshot */}
      {!data.snapshot_summary && data.summary && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-3">摘要</h2>
          <p className="text-gray-700 leading-relaxed">{data.summary}</p>
          {data.business_angle && (
            <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-4">
              <p className="text-sm font-medium text-amber-800">商业机会</p>
              <p className="text-amber-700 mt-1">{data.business_angle}</p>
            </div>
          )}
        </section>
      )}

      {/* Module Picker */}
      {pillars.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">深度分析</h2>
          <p className="text-sm text-gray-500 mb-4">
            选择你感兴趣的分析维度，AI 将对每个维度进行深入分析。
          </p>

          <div className="space-y-6">
            {pillars.map((pillar) => (
              <div key={pillar.key}>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">{pillar.display_name}</h3>
                <p className="text-xs text-gray-400 mb-3">{pillar.description}</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {pillar.modules.map((m) => (
                    <ModuleCheckbox
                      key={m.key}
                      module={m}
                      checked={selectedModules.has(m.key)}
                      onChange={toggleModule}
                      isEnriching={isEnriching}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={handleEnrich}
            disabled={pendingCount === 0 || isEnriching}
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isEnriching ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                分析中...
              </>
            ) : (
              <>开始分析 ({pendingCount} 个模块)</>
            )}
          </button>
        </section>
      )}

      {/* New enrichment results from enrichment_data */}
      {enrichmentData &&
        Object.keys(enrichmentData).length > 0 &&
        renderModuleResults(enrichmentData)}

      {/* Legacy enriched sections (backward compatible) */}
      {demandValidation && !enrichmentData?.demand_validation && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">需求真实性分析</h2>
          {!demandValidation.is_genuine_demand && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              该需求被判定为可能不够真实，请谨慎参考以下分析。
            </div>
          )}
          <AnalysisField label="判断依据" text={demandValidation.validation_reasoning} />
          <AnalysisField label="来源证据" text={demandValidation.evidence_from_sources} />
          <AnalysisField label="频率分析" text={demandValidation.frequency_analysis} />
          <AnalysisField label="用户情绪强度" text={demandValidation.user_sentiment_intensity} />
        </section>
      )}

      {marketValue && !enrichmentData?.market_value_analysis && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">市场价值分析</h2>
          <AnalysisField label="市场规模估算" text={marketValue.market_size_estimate} />
          <AnalysisField label="目标用户群体" text={marketValue.target_audience} />
          <AnalysisField label="付费意愿证据" text={marketValue.willingness_to_pay_evidence} />
          <AnalysisField label="竞争格局" text={marketValue.competition_landscape} />
          <AnalysisField label="变现潜力" text={marketValue.monetization_potential} />
        </section>
      )}

      {implementation && !enrichmentData?.implementation_plan && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">落地实施方案</h2>
          <div className="mb-4 rounded-lg bg-indigo-50 border border-indigo-200 p-4">
            <p className="text-sm font-medium text-indigo-800 mb-1">MVP 范围</p>
            <p className="text-indigo-700 text-sm">{implementation.mvp_scope}</p>
          </div>
          <AnalysisField label="技术方案" text={implementation.technical_approach} />
          {implementation.recommended_tech_stack.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">推荐技术栈</p>
              <div className="flex flex-wrap gap-1.5">
                {implementation.recommended_tech_stack.map((tech: string) => (
                  <span
                    key={tech}
                    className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}
          <AnalysisField label="技术选型理由" text={implementation.tech_stack_rationale} />
          <AnalysisField label="推广策略" text={implementation.go_to_market_strategy} />
          <AnalysisField label="盈利模式" text={implementation.monetization_model} />
        </section>
      )}

      {soloFeasibility && !enrichmentData?.solo_feasibility && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">个人可行性评估</h2>
          <AnalysisField label="具体障碍" text={soloFeasibility.specific_barriers} />
          <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-4">
            <p className="text-sm font-medium text-green-800 mb-1">如何克服</p>
            <p className="text-green-700 text-sm">{soloFeasibility.how_to_overcome}</p>
          </div>
          <div className="mb-4 rounded-lg bg-purple-50 border border-purple-200 p-4">
            <p className="text-sm font-medium text-purple-800 mb-1">预估开发周期</p>
            <p className="text-purple-700 text-lg font-bold">{soloFeasibility.realistic_dev_time}</p>
            <p className="text-purple-600 text-xs mt-1">{soloFeasibility.dev_time_reasoning}</p>
          </div>
        </section>
      )}

      {/* Score breakdown */}
      {breakdown && dimensions.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-2">
            痛点强度分 ({breakdown.total_score.toFixed(1)})
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            机会分 = 痛点强度 &times; 0.4 + 个人可行性 &times; 0.6
          </p>
          <div className="space-y-3">
            {dimensions.map((d) => {
              const raw = (breakdown as unknown as Record<string, number>)[d.key] ?? 0;
              const isReversed = d.key === "automation_difficulty";
              const displayVal = isReversed ? 10 - raw : raw;
              const contrib = displayVal * d.w;
              return (
                <div key={d.key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{d.label}</span>
                    <span className="text-gray-500">
                      {isReversed
                        ? `(10 - ${raw.toFixed(1)}) × ${d.w.toFixed(2)} = ${contrib.toFixed(2)}`
                        : `${raw.toFixed(1)} × ${d.w.toFixed(2)} = ${contrib.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-indigo-500 transition-all"
                      style={{ width: `${(displayVal / 10) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Sources */}
      {data.source_findings.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">来源 ({data.source_findings.length})</h2>
          <div className="space-y-3">
            {data.source_findings.map((src, i) =>
              src.url ? (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-lg border border-gray-100 p-4 hover:bg-gray-50 transition-colors"
                >
                  <p className="font-medium text-gray-900 text-sm">{src.title}</p>
                  <div className="flex gap-3 mt-1 text-xs text-gray-500">
                    {src.platform && <span>{src.platform}</span>}
                    {src.snippet && <span className="truncate max-w-md">{src.snippet}</span>}
                  </div>
                </a>
              ) : (
                <div key={i} className="rounded-lg border border-gray-100 p-4">
                  <p className="font-medium text-gray-900 text-sm">{src.title}</p>
                  {src.platform && <span className="text-xs text-gray-500 mt-1">{src.platform}</span>}
                </div>
              )
            )}
          </div>
        </section>
      )}

      {/* Related */}
      {data.related.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">相关需求</h2>
          <div className="space-y-2">
            {data.related.map((r) => (
              <Link
                key={r.id}
                href={`/pain-points/${r.id}`}
                className="flex items-center justify-between rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors"
              >
                <span className="text-sm text-gray-900">{r.title}</span>
                <span
                  className={`text-sm font-bold ${scoreColor(toDisplayScore(r.opportunity_score, r.pain_score))}`}
                >
                  {formatScore(toDisplayScore(r.opportunity_score, r.pain_score))}
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function EnrichedSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6">
      <h2 className="font-semibold text-gray-900 mb-4">{title}</h2>
      {children}
    </section>
  );
}

const MODULE_RENDERERS: Record<
  string,
  { title: string; render: (result: Record<string, unknown>) => React.ReactNode }
> = {
  market_size: {
    title: "市场规模估算",
    render: (r) => (
      <>
        <AnalysisField label="潜在用户量级" text={r.total_addressable_users as string} />
        <AnalysisField label="市场分类" text={r.market_size_category as string} />
        <AnalysisField label="发展阶段" text={r.growth_stage as string} />
        <AnalysisField label="分析依据" text={r.evidence as string} />
        <AnalysisField label="确定性说明" text={r.confidence_note as string} />
      </>
    ),
  },
  target_user: {
    title: "目标用户画像",
    render: (r) => (
      <>
        <AnalysisField label="核心用户" text={r.primary_users as string} />
        <AnalysisField label="次要用户" text={r.secondary_users as string} />
        <AnalysisField
          label="使用场景"
          text={Array.isArray(r.use_scenarios) ? (r.use_scenarios as string[]).join("；") : String(r.use_scenarios || "")}
        />
        <AnalysisField label="付费决策链" text={r.decision_chain as string} />
        <AnalysisField label="痛点强度" text={r.pain_intensity as string} />
      </>
    ),
  },
  willingness_to_pay: {
    title: "付费意愿分析",
    render: (r) => (
      <>
        <AnalysisField label="现有付费方案" text={r.has_paying_alternatives as string} />
        <AnalysisField label="建议定价区间" text={r.expected_price_range as string} />
        <AnalysisField label="付费意愿等级" text={r.willingness_category as string} />
        <AnalysisField label="定价依据" text={r.evidence as string} />
        <AnalysisField label="价格敏感度" text={r.pricing_sensitivity as string} />
      </>
    ),
  },
  mvp_definition: {
    title: "MVP 产品定义",
    render: (r) => (
      <>
        <div className="mb-4 rounded-lg bg-indigo-50 border border-indigo-200 p-4">
          <p className="text-sm font-medium text-indigo-800 mb-2">核心功能</p>
          <ul className="list-disc list-inside text-indigo-700 text-sm space-y-1">
            {(r.core_features as string[])?.map((f: string, i: number) => <li key={i}>{f}</li>)}
          </ul>
        </div>
        <AnalysisField label="范围边界" text={r.scope_boundary as string} />
        <AnalysisField label="用户旅程" text={r.user_journey as string} />
        <AnalysisField label="时间建议" text={r.mvp_timeline as string} />
        {r.success_metrics && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600 mb-1">成功指标</p>
            <ul className="list-disc list-inside text-sm text-gray-800 space-y-1">
              {(r.success_metrics as string[])?.map((m: string, i: number) => <li key={i}>{m}</li>)}
            </ul>
          </div>
        )}
      </>
    ),
  },
  tech_approach: {
    title: "技术方案推荐",
    render: (r) => {
      const stack = r.recommended_stack as Record<string, string> | undefined;
      return (
        <>
          {stack && (
            <div className="mb-4 grid grid-cols-2 gap-2">
              {Object.entries(stack).map(([k, v]) => (
                <div key={k} className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium text-gray-500 capitalize">{k}</p>
                  <p className="text-sm text-gray-800">{v}</p>
                </div>
              ))}
            </div>
          )}
          <AnalysisField label="架构概述" text={r.architecture_overview as string} />
          <AnalysisField label="技术选型理由" text={r.stack_rationale as string} />
          {r.key_technical_challenges && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-600 mb-1">技术难点</p>
              <ul className="list-disc list-inside text-sm text-gray-800 space-y-1">
                {(r.key_technical_challenges as string[])?.map((c: string, i: number) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          )}
        </>
      );
    },
  },
  dev_timeline: {
    title: "开发周期估算",
    render: (r) => (
      <>
        <div className="mb-4 rounded-lg bg-purple-50 border border-purple-200 p-4">
          <p className="text-lg font-bold text-purple-700">{r.total_estimate as string}</p>
          <p className="text-xs text-purple-500 mt-1">{r.assumptions as string}</p>
        </div>
        <AnalysisField label="并行推进" text={r.parallel_work as string} />
        <AnalysisField label="风险缓冲" text={r.risk_buffer as string} />
        {r.phases && (
          <div className="space-y-2">
            {(r.phases as Array<{ phase: string; duration: string; tasks: string[] }>)?.map(
              (p: { phase: string; duration: string; tasks: string[] }, i: number) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{p.phase}</span>
                    <span className="text-xs text-gray-500">{p.duration}</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-gray-600 space-y-0.5">
                    {p.tasks?.map((t: string, j: number) => <li key={j}>{t}</li>)}
                  </ul>
                </div>
              )
            )}
          </div>
        )}
      </>
    ),
  },
  go_to_market: {
    title: "推广获客策略",
    render: (r) => (
      <>
        <AnalysisField label="冷启动策略" text={r.launch_strategy as string} />
        <AnalysisField label="内容策略" text={r.content_strategy as string} />
        <AnalysisField label="增长飞轮" text={r.growth_loops as string} />
        {r.acquisition_channels && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600 mb-1">获客渠道</p>
            {(r.acquisition_channels as Array<{ channel: string; tactics: string; expected_cost: string }>)?.map(
              (c: { channel: string; tactics: string; expected_cost: string }, i: number) => (
                <div key={i} className="text-sm text-gray-800 mb-1">
                  <span className="font-medium">{c.channel}</span>：{c.tactics}（成本：{c.expected_cost}）
                </div>
              )
            )}
          </div>
        )}
      </>
    ),
  },
  monetization_model: {
    title: "盈利模式设计",
    render: (r) => (
      <>
        <AnalysisField label="推荐模式" text={r.recommended_model as string} />
        {r.pricing_tiers && (
          <div className="mb-4 space-y-2">
            {(r.pricing_tiers as Array<{ tier: string; price: string; features: string[]; target_user: string }>)?.map(
              (t: { tier: string; price: string; features: string[]; target_user: string }, i: number) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{t.tier}</span>
                    <span className="text-sm font-bold text-indigo-600">{t.price}</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-gray-600">
                    {t.features?.map((f: string, j: number) => <li key={j}>{f}</li>)}
                  </ul>
                </div>
              )
            )}
          </div>
        )}
        <AnalysisField label="收入预测" text={r.revenue_projections as string} />
      </>
    ),
  },
  competitor_scan: {
    title: "现有竞品扫描",
    render: (r) => (
      <>
        <AnalysisField label="市场成熟度" text={r.market_maturity as string} />
        {r.direct_competitors && (
          <div className="mb-4 space-y-2">
            {(r.direct_competitors as Array<{ name: string; type: string; brief: string; estimated_users: string }>)?.map(
              (c: { name: string; type: string; brief: string; estimated_users: string }, i: number) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-gray-800">{c.name}</span>
                    <span className="text-xs bg-gray-100 rounded px-1.5 py-0.5 text-gray-500">{c.type}</span>
                    {c.estimated_users && (
                      <span className="text-xs text-gray-400">{c.estimated_users}</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">{c.brief}</p>
                </div>
              )
            )}
          </div>
        )}
        <AnalysisField label="扫描说明" text={r.scan_scope as string} />
      </>
    ),
  },
  competitor_compare: {
    title: "竞品优劣势对比",
    render: (r) => (
      <>
        <AnalysisField label="竞品共同优势" text={r.common_strengths as string} />
        <AnalysisField label="竞品共同劣势" text={r.common_weaknesses as string} />
        {r.user_complaints && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-100 p-4">
            <p className="text-sm font-medium text-red-700 mb-2">用户常见抱怨</p>
            <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
              {(r.user_complaints as string[])?.map((c: string, i: number) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        )}
        <div className="rounded-lg bg-indigo-50 border border-indigo-200 p-4">
          <p className="text-sm font-medium text-indigo-800 mb-1">关键洞察</p>
          <p className="text-indigo-700 text-sm">{r.key_insight as string}</p>
        </div>
      </>
    ),
  },
  differentiation: {
    title: "差异化切入点",
    render: (r) => (
      <>
        <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-4">
          <p className="text-sm font-medium text-green-800 mb-1">独特价值主张</p>
          <p className="text-green-700 text-sm">{r.unique_value_proposition as string}</p>
        </div>
        {r.differentiation_angles && (
          <div className="mb-4 space-y-2">
            {(r.differentiation_angles as Array<{ angle: string; description: string; why_competitors_cant_easily_copy: string }>)?.map(
              (d: { angle: string; description: string; why_competitors_cant_easily_copy: string }, i: number) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <p className="text-sm font-medium text-gray-800">{d.angle}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{d.description}</p>
                  <p className="text-xs text-gray-400 mt-0.5">壁垒：{d.why_competitors_cant_easily_copy}</p>
                </div>
              )
            )}
          </div>
        )}
        <AnalysisField label="护城河分析" text={r.defensibility as string} />
      </>
    ),
  },
  market_gap: {
    title: "市场空白机会",
    render: (r) => (
      <>
        <div className="mb-4 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <p className="text-sm font-medium text-blue-800 mb-1">建议切入点</p>
          <p className="text-blue-700 text-sm">{r.recommended_entry_point as string}</p>
        </div>
        {r.unmet_needs && (
          <div className="mb-4 space-y-2">
            {(r.unmet_needs as Array<{ need: string; why_unmet: string; opportunity_size: string }>)?.map(
              (n: { need: string; why_unmet: string; opportunity_size: string }, i: number) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex justify-between mb-0.5">
                    <span className="text-sm font-medium text-gray-800">{n.need}</span>
                    <span className="text-xs text-gray-400">{n.opportunity_size}</span>
                  </div>
                  <p className="text-xs text-gray-600">为什么未被满足：{n.why_unmet}</p>
                </div>
              )
            )}
          </div>
        )}
      </>
    ),
  },
};

function renderModuleResults(
  enrichmentData: Record<string, { completed_at: string; result: unknown }>
) {
  const rendered: React.ReactNode[] = [];
  for (const key of Object.keys(enrichmentData)) {
    const renderer = MODULE_RENDERERS[key];
    if (!renderer) continue;
    rendered.push(
      <EnrichedSection key={key} title={renderer.title}>
        {renderer.render((enrichmentData[key].result || {}) as Record<string, unknown>)}
      </EnrichedSection>
    );
  }
  return <>{rendered}</>;
}
