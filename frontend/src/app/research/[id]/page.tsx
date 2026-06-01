"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import PainCard from "@/components/ui/PainCard";
import {
  getResearchJob,
  getResearchPainPoints,
  type ResearchJob,
  type PainPoint,
} from "@/lib/api";

export default function ResearchDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [painPoints, setPainPoints] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const jobRes = await getResearchJob(Number(id));
      if (!jobRes.success || !jobRes.data) {
        setError("研究任务未找到");
        setLoading(false);
        return;
      }
      setJob(jobRes.data);

      const ppRes = await getResearchPainPoints(Number(id), {
        per_page: "50",
      });
      if (ppRes.success && ppRes.data) {
        setPainPoints(ppRes.data);
      }
      setLoading(false);
    }
    load();

    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [id]);

  if (loading) {
    return (
      <div className="text-center py-16 text-gray-400">
        <div className="animate-pulse text-lg">加载中...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg">{error || "数据加载失败"}</p>
        <Link href="/" className="text-sm text-indigo-600 mt-2 inline-block">
          返回首页
        </Link>
      </div>
    );
  }

  const statusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成";
      case "running":
        return "运行中";
      case "failed":
        return "失败";
      default:
        return "等待中";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          &larr; 返回
        </Link>
        <h1 className="text-xl font-bold text-gray-900">{job.domain}</h1>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            job.status === "completed"
              ? "text-emerald-600 bg-emerald-50"
              : job.status === "running"
                ? "text-amber-600 bg-amber-50"
                : "text-red-600 bg-red-50"
          }`}
        >
          {statusLabel(job.status)}
        </span>
      </div>

      <div className="flex gap-6 text-sm text-gray-500">
        <span>平台: {job.platforms?.join(", ") || "-"}</span>
        <span>搜索到 {job.total_findings} 条内容</span>
        <span>提取 {job.pain_points_extracted} 个需求</span>
        {job.completed_at && (
          <span>
            完成于 {new Date(job.completed_at).toLocaleString("zh-CN")}
          </span>
        )}
      </div>

      {job.status === "running" && (
        <div className="text-center py-8">
          <div className="animate-pulse text-gray-400">
            正在搜索和分析，请稍候...
          </div>
        </div>
      )}

      {job.status === "failed" && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          研究失败: {job.error_message || "未知错误"}
        </div>
      )}

      {job.status === "completed" && painPoints.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">未找到需求</p>
          <p className="text-sm mt-2">该领域未发现明显痛点，请尝试其他领域。</p>
        </div>
      )}

      {painPoints.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">
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
  );
}
