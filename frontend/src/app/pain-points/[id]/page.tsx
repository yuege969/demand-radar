"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getPainPoint, type PainPointDetail } from "@/lib/api";
import { formatDate, formatScore, scoreColor, toDisplayScore } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

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

      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="font-semibold text-gray-900 mb-3">AI 分析摘要</h2>
        <p className="text-gray-700 leading-relaxed">{data.summary}</p>
        {data.business_angle && (
          <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-4">
            <p className="text-sm font-medium text-amber-800">商业机会</p>
            <p className="text-amber-700 mt-1">{data.business_angle}</p>
          </div>
        )}
      </section>

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

      {data.source_posts.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">来源帖子 ({data.source_posts.length})</h2>
          <div className="space-y-3">
            {data.source_posts.map((post) => (
              <a
                key={post.id}
                href={post.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-lg border border-gray-100 p-4 hover:bg-gray-50 transition-colors"
              >
                <p className="font-medium text-gray-900 text-sm">{post.title}</p>
                <div className="flex gap-3 mt-1 text-xs text-gray-500">
                  <span>r/{post.subreddit}</span>
                  <span>{post.score} 赞</span>
                  <span>{post.num_comments} 评论</span>
                  <span>{formatDate(post.created_utc)}</span>
                </div>
              </a>
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
