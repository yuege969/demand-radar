"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import PainCard from "@/components/ui/PainCard";
import ScrollRestoration from "@/components/common/ScrollRestoration";
import { getResearchJob, getResearchPainPoints, reEnrichJob, type ResearchJob, type PainPoint } from "@/lib/api";

export default function ResearchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [painPoints, setPainPoints] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrichMsg, setEnrichMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    const MAX_ATTEMPTS = 60;
    const BASE_DELAY = 3000;
    const MAX_DELAY = 30000;

    async function load() {
      const jobRes = await getResearchJob(Number(id));
      if (cancelled) return;
      if (!jobRes.success || !jobRes.data) {
        setError("研究任务未找到");
        setLoading(false);
        return;
      }
      setJob(jobRes.data);

      const isDone = jobRes.data.status === "completed" || jobRes.data.status === "failed";
      const shouldStop = isDone && !jobRes.data.is_enriching;

      if (isDone || attempt === 0) {
        const ppRes = await getResearchPainPoints(Number(id), { per_page: "50" });
        if (cancelled) return;
        if (ppRes.success && ppRes.data) setPainPoints(ppRes.data);
      }
      setLoading(false);

      if (shouldStop || attempt >= MAX_ATTEMPTS) return;

      attempt++;
      const delay = Math.min(BASE_DELAY * Math.pow(1.3, attempt), MAX_DELAY);
      timeout = setTimeout(() => { if (!cancelled) load(); }, delay);
    }

    load();

    return () => { cancelled = true; if (timeout) clearTimeout(timeout); };
  }, [id]);

  if (loading) {
    return (
      <div className="text-center py-16 text-text-muted">
        <div className="animate-pulse text-lg">加载中...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="text-center py-16 text-text-muted">
        <p className="text-lg">{error || "数据加载失败"}</p>
        <Link href="/" className="text-sm text-accent mt-2 inline-block">返回首页</Link>
      </div>
    );
  }

  const statusLabel = (status: string) => {
    switch (status) { case "completed": return "已完成"; case "running": return "运行中"; case "failed": return "失败"; default: return "等待中"; }
  };

  const statusStyle = (status: string) => {
    switch (status) {
      case "completed": return "text-green bg-green-muted";
      case "running": return "text-amber bg-amber-muted";
      case "failed": return "text-red bg-red-muted";
      default: return "text-text-muted bg-surface-2";
    }
  };

  async function handleReEnrich() {
    setEnrichMsg("");
    const res = await reEnrichJob(Number(id));
    if (res.success) { setEnrichMsg(res.data?.message || ""); }
    else { setEnrichMsg(res.error || "请求失败"); }
  }

  return (
    <ScrollRestoration>
      <div className="space-y-6">
        <div className="flex items-center gap-3 flex-wrap">
          <Link href="/" className="text-[13px] text-text-muted hover:text-text-secondary transition-colors">
            &larr; 返回
          </Link>
          <h1 className="text-lg font-semibold text-text-primary">{job.domain}</h1>
          <span className={`text-[11px] px-2 py-0.5 rounded-md font-medium ${statusStyle(job.status)}`}>
            {statusLabel(job.status)}
          </span>
          {job.status === "completed" && (
            job.is_enriching ? (
              <span className="inline-flex items-center gap-1 rounded-md bg-accent-muted px-2.5 py-1 text-[11px] font-medium text-accent">
                <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                AI 分析中...
              </span>
            ) : (
              <button
                onClick={handleReEnrich}
                className="inline-flex items-center gap-1 rounded-lg border border-hairline bg-surface-1 px-2.5 py-1 text-[11px] text-text-secondary hover:text-text-primary hover:border-white/10 transition-colors"
              >
                重新 AI 分析
              </button>
            )
          )}
          {enrichMsg && <span className="text-[11px] text-text-muted">{enrichMsg}</span>}
        </div>

        <div className="flex gap-6 text-[13px] text-text-muted flex-wrap">
          <span>平台: {job.platforms?.join(", ") || "-"}</span>
          <span>搜索到 {job.total_findings} 条内容</span>
          <span>提取 {job.pain_points_extracted} 个需求</span>
          {job.completed_at && <span>完成于 {new Date(job.completed_at).toLocaleString("zh-CN")}</span>}
        </div>

        {job.status === "running" && (
          <div className="text-center py-8 space-y-4">
            <div className="animate-pulse text-text-muted text-lg">正在搜索和分析，请稍候...</div>
            <div className="flex justify-center gap-3">
              {[
                { label: "搜索中", active: true },
                { label: "提取中", active: job.total_findings > 0 },
                { label: "富化中", active: job.pain_points_extracted > 0 },
                { label: "完成", active: false },
              ].map((stage) => (
                <span
                  key={stage.label}
                  className={`inline-flex items-center rounded-md px-3 py-1 text-[11px] font-medium ${
                    stage.active ? "bg-accent-muted text-accent" : "bg-surface-2 text-text-muted"
                  }`}
                >
                  {stage.active && <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current animate-pulse" />}
                  {stage.label}
                </span>
              ))}
            </div>
          </div>
        )}

        {job.status === "failed" && (
          <div className="rounded-lg border border-red/20 bg-red-muted px-4 py-3 text-[13px] text-red">
            <p className="font-semibold">研究失败</p>
            <p className="mt-1 opacity-80">{job.error_message || "未知错误，请稍后重试"}</p>
            <a href="/" className="inline-block mt-3 text-sm text-accent hover:underline">返回首页重新开始</a>
          </div>
        )}

        {job.status === "completed" && painPoints.length === 0 && (
          <div className="text-center py-16 text-text-muted">
            <p className="text-lg">未找到需求</p>
            <p className="text-sm mt-2">该领域未发现明显痛点，请尝试其他领域。</p>
          </div>
        )}

        {painPoints.length > 0 && (
          <section>
            <h2 className="text-[15px] font-semibold text-text-primary mb-4">
              发现的需求 ({painPoints.length})
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {painPoints.map((pp) => (
                <PainCard key={pp.id} painPoint={pp} />
              ))}
            </div>
          </section>
        )}
      </div>
    </ScrollRestoration>
  );
}
