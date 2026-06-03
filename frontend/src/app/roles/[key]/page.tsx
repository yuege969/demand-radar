"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getRoleDetail, triggerResearch, type Role, type PainPoint } from "@/lib/api";
import PainCard from "@/components/ui/PainCard";

const TOKEN_STORAGE_KEY = "demand-radar-admin-token";

export default function RoleDetailPage() {
  const params = useParams();
  const key = String(params.key);
  const router = useRouter();

  const [role, setRole] = useState<Role | null>(null);
  const [related, setRelated] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [researching, setResearching] = useState(false);
  const [researchMessage, setResearchMessage] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    const res = await getRoleDetail(key);
    if (res.success && res.data) {
      setRole(res.data.role);
      setRelated(res.data.related_pain_points);
    } else {
      setError(res.error || "加载失败");
    }
    setLoading(false);
  }, [key]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartResearch = async (subtopic?: string) => {
    const domain = subtopic
      ? `${role?.name} ${subtopic} 痛点`
      : `${role?.name} 痛点`;

    setResearching(true);
    setResearchMessage("");

    const token = localStorage.getItem(TOKEN_STORAGE_KEY) || "";
    const res = await triggerResearch(domain, token);

    if (res.success && res.data) {
      const data = res.data as { job_id?: number };
      if (data.job_id) {
        router.push(`/research/${data.job_id}`);
      } else {
        setResearchMessage("研究已启动，稍后刷新查看");
      }
    } else {
      setResearchMessage(res.error || "启动失败，请确认已设置 Admin Token");
    }
    setResearching(false);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-gray-200" />
        <div className="h-4 w-96 rounded bg-gray-100" />
        <div className="h-32 rounded-xl bg-gray-100" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-48 rounded-xl bg-gray-100" />
          <div className="h-48 rounded-xl bg-gray-100" />
        </div>
      </div>
    );
  }

  if (error || !role) {
    return (
      <div className="text-center py-20">
        <p className="text-lg text-gray-500">角色未找到</p>
        <Link href="/" className="text-indigo-600 hover:underline mt-2 inline-block">
          返回首页
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <Link href="/" className="text-sm text-gray-500 hover:text-indigo-600">
        &larr; 返回首页
      </Link>

      {/* Role header */}
      <header className="rounded-xl border border-gray-200 bg-white p-6">
        <div className="flex items-start gap-4">
          <span className="text-4xl">{role.icon}</span>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{role.name}</h1>
            <p className="text-gray-600 mt-2">{role.description}</p>
            {role.demand_count > 0 && (
              <div className="flex items-center gap-3 mt-3 text-sm text-gray-500">
                <span>{role.demand_count} 个已有需求</span>
                {role.avg_opportunity_score > 0 && (
                  <span className="text-amber-600 font-medium">
                    平均 {role.avg_opportunity_score.toFixed(0)} 分
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Subtopics + research trigger */}
      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="font-semibold text-gray-900 mb-1">研究方向</h2>
        <p className="text-sm text-gray-500 mb-4">
          选择一个具体方向开始研究，或直接研究整个角色群体
        </p>

        <div className="flex flex-wrap gap-2 mb-6">
          {role.subtopics.map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => handleStartResearch(st)}
              disabled={researching}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors"
            >
              {st}
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => handleStartResearch()}
          disabled={researching}
          className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {researching ? (
            <span className="inline-flex items-center gap-2">
              <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
              研究启动中...
            </span>
          ) : (
            `开始研究「${role.name}」的全部需求`
          )}
        </button>

        {researchMessage && (
          <p className="mt-3 text-sm text-gray-600">{researchMessage}</p>
        )}
      </section>

      {/* Pain point vocabulary hint */}
      <section className="rounded-xl border border-orange-200 bg-orange-50 p-4">
        <p className="text-sm text-orange-800">
          <span className="font-medium">提示：</span>
          想获得更精准的结果？在首页的「痛点词库」中选择情绪关键词（如"烦死了"、"有没有工具"），然后结合 {role.name} 的子主题一起搜索，会发现更多隐藏的真实需求。
        </p>
      </section>

      {/* Related pain points */}
      {related.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            已有相关需求 ({related.length})
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {related.map((pp) => (
              <PainCard key={pp.id} painPoint={pp} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
