"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getPainPoint,
  type PainPointDetail,
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

export default function PainPointDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [data, setData] = useState<PainPointDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getPainPoint(id).then((res) => {
      if (res.success && res.data) setData(res.data);
      setLoading(false);
    });
  }, [id]);

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
        <Link href="/" className="text-indigo-600 hover:underline mt-2 inline-block">返回首页</Link>
      </div>
    );
  }

  const breakdown = data.score_breakdown;
  const dimensions = breakdown ? [
    { key: "emotion_intensity", label: "情绪强度", w: 0.20 },
    { key: "comment_volume", label: "讨论热度", w: 0.15 },
    { key: "repeat_frequency", label: "重复频率", w: 0.20 },
    { key: "involves_money", label: "付费意愿", w: 0.20 },
    { key: "has_paid_solution", label: "已有方案", w: 0.10 },
    { key: "automation_difficulty", label: "实现难度", w: 0.10 },
    { key: "is_long_term", label: "长期需求", w: 0.05 },
  ] : [];

  const demandValidation = parseAnalysis<DemandValidation>(data.demand_validation);
  const marketValue = parseAnalysis<MarketValueAnalysis>(data.market_value_analysis);
  const implementation = parseAnalysis<ImplementationPlan>(data.implementation_plan);
  const soloFeasibility = parseAnalysis<SoloFeasibility>(data.solo_feasibility);
  const hasEnriched = data.enriched_at !== null;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <Link href="/" className="text-sm text-gray-500 hover:text-indigo-600">&larr; 返回列表</Link>

      <header className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
          <div className="shrink-0 text-right">
            <span className={`text-3xl font-bold ${scoreColor(toDisplayScore(data.opportunity_score, data.pain_score))}`}>
              {formatScore(toDisplayScore(data.opportunity_score, data.pain_score))}
            </span>
            {data.opportunity_score > 0 && (
              <p className="text-xs text-gray-400 mt-0.5">机会分</p>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.is_individual_feasible ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              个人可做
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
              门槛较高
            </span>
          )}
          {data.estimated_dev_time && (
            <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700">
              {data.estimated_dev_time}
            </span>
          )}
          {data.market_saturation && (
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
              data.market_saturation === "green" ? "bg-blue-100 text-blue-700" :
              data.market_saturation === "amber" ? "bg-yellow-100 text-yellow-700" :
              "bg-red-100 text-red-700"
            }`}>
              {data.market_saturation === "green" ? "蓝海" : data.market_saturation === "amber" ? "中等" : "红海"}
            </span>
          )}
          {data.category && <Badge label={data.category} variant="category" />}
          {data.industry && <Badge label={data.industry} variant="industry" />}
          {data.is_saas_idea && <Badge label="SaaS 机会" variant="saas" />}
          {data.is_plugin_idea && <Badge label="插件机会" variant="plugin" />}
        </div>
      </header>

      {!hasEnriched && data.summary && (
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

      {demandValidation && (
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

      {marketValue && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">市场价值分析</h2>
          <AnalysisField label="市场规模估算" text={marketValue.market_size_estimate} />
          <AnalysisField label="目标用户群体" text={marketValue.target_audience} />
          <AnalysisField label="付费意愿证据" text={marketValue.willingness_to_pay_evidence} />
          <AnalysisField label="竞争格局" text={marketValue.competition_landscape} />
          <AnalysisField label="变现潜力" text={marketValue.monetization_potential} />
        </section>
      )}

      {implementation && (
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
                  <span key={tech} className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
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

      {soloFeasibility && (
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

      {breakdown && dimensions.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-2">痛点强度分 ({breakdown.total_score.toFixed(1)})</h2>
          <p className="text-xs text-gray-500 mb-4">机会分 = 痛点强度 &times; 0.4 + 个人可行性 &times; 0.6</p>
          <div className="space-y-3">
            {dimensions.map((d) => {
              const val = (breakdown as unknown as Record<string, number>)[d.key] ?? 0;
              return (
                <div key={d.key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{d.label}</span>
                    <span className="text-gray-500">
                      {val.toFixed(1)} &times; {d.w.toFixed(2)} = {(val * d.w).toFixed(2)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-indigo-500 transition-all"
                      style={{ width: `${(val / 10) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {data.source_findings.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">来源 ({data.source_findings.length})</h2>
          <div className="space-y-3">
            {data.source_findings.map((src, i) => (
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
            ))}
          </div>
        </section>
      )}

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
                <span className={`text-sm font-bold ${scoreColor(toDisplayScore(r.opportunity_score, r.pain_score))}`}>
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
