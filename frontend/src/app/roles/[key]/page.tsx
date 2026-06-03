"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getRoleDetail, triggerResearch, type Role, type PainPoint } from "@/lib/api";
import PainCard from "@/components/ui/PainCard";
import ScrollRestoration from "@/components/common/ScrollRestoration";

const TOKEN_STORAGE_KEY = "demand-radar-admin-token";

const ROLE_ICONS: Record<string, React.ReactNode> = {
  programmer: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L21 12l-3.75 5.25M6.75 17.25L3 12l3.75-5.25M14.25 3.75l-4.5 16.5" />
    </svg>
  ),
  content_creator: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
    </svg>
  ),
  teacher: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  ),
  hr: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  lawyer: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
    </svg>
  ),
  cross_border_seller: (
    <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
    </svg>
  ),
};

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

  useEffect(() => { loadData(); }, [loadData]);

  const handleStartResearch = async (subtopic?: string) => {
    const domain = subtopic ? `${role?.name} ${subtopic} 痛点` : `${role?.name} 痛点`;
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
        <div className="h-8 w-48 rounded bg-surface-2" />
        <div className="h-4 w-96 rounded bg-surface-1" />
        <div className="h-32 rounded-[10px] bg-surface-1" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-48 rounded-[10px] bg-surface-1" />
          <div className="h-48 rounded-[10px] bg-surface-1" />
        </div>
      </div>
    );
  }

  if (error || !role) {
    return (
      <div className="text-center py-20">
        <p className="text-lg text-text-secondary">角色未找到</p>
        <Link href="/" className="text-accent hover:underline mt-2 inline-block text-sm">返回首页</Link>
      </div>
    );
  }

  const iconNode = ROLE_ICONS[role.key] || ROLE_ICONS.programmer;

  return (
    <ScrollRestoration>
      <div className="max-w-4xl mx-auto space-y-8">
        <Link href="/" className="text-[13px] text-text-muted hover:text-text-secondary transition-colors">
          &larr; 返回首页
        </Link>

        <header className="rounded-[10px] border border-hairline bg-surface-1 p-6">
          <div className="flex items-start gap-4">
            <div className="text-accent">{iconNode}</div>
            <div className="flex-1">
              <h1 className="text-xl font-semibold text-text-primary">{role.name}</h1>
              <p className="text-text-secondary mt-2 text-[14px] leading-relaxed">{role.description}</p>
              {role.demand_count > 0 && (
                <div className="flex items-center gap-3 mt-3 text-[13px] text-text-muted font-mono">
                  <span>{role.demand_count} 个已有需求</span>
                  {role.avg_opportunity_score > 0 && (
                    <span className="text-amber font-medium">平均 {role.avg_opportunity_score.toFixed(0)} 分</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        <section className="rounded-[10px] border border-hairline bg-surface-1 p-6">
          <h2 className="text-[15px] font-semibold text-text-primary mb-1">研究方向</h2>
          <p className="text-[13px] text-text-secondary mb-4">
            选择一个具体方向开始研究，或直接研究整个角色群体
          </p>

          <div className="flex flex-wrap gap-2 mb-6">
            {role.subtopics.map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => handleStartResearch(st)}
                disabled={researching}
                className="inline-flex items-center gap-1.5 rounded-lg border border-accent/20 bg-accent-muted px-3 py-2 text-[13px] font-medium text-accent hover:bg-accent/20 disabled:opacity-50 transition-colors"
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
            className="w-full rounded-lg bg-accent px-4 py-3 text-[13px] font-medium text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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

          {researchMessage && <p className="mt-3 text-[13px] text-text-secondary">{researchMessage}</p>}
        </section>

        <section className="rounded-[10px] border border-amber/20 bg-amber-muted p-4">
          <p className="text-[13px] text-amber leading-relaxed">
            <span className="font-semibold">提示：</span>
            想获得更精准的结果？在首页的「痛点词库」中选择情绪关键词（如"烦死了"、"有没有工具"），然后结合 {role.name} 的子主题一起搜索，会发现更多隐藏的真实需求。
          </p>
        </section>

        {related.length > 0 && (
          <section>
            <h2 className="text-[15px] font-semibold text-text-primary mb-4">
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
    </ScrollRestoration>
  );
}
