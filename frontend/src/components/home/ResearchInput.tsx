"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  triggerResearch,
  getResearchJobs,
  type ResearchJob,
} from "@/lib/api";

const TOKEN_STORAGE_KEY = "demand-radar-admin-token";

export default function ResearchInput() {
  const router = useRouter();
  const [domain, setDomain] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (saved) setToken(saved);
  }, []);

  const fetchJobs = useCallback(async () => {
    const res = await getResearchJobs({ per_page: "5" });
    if (res.success && res.data) {
      setJobs(res.data);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain.trim()) return;

    setLoading(true);
    setMessage("");

    try {
      const res = await triggerResearch(
        domain.trim(),
        token.trim()
      );
      if (res.success && res.data) {
        const data = res.data as { job_id?: number };
        if (token.trim()) {
          localStorage.setItem(TOKEN_STORAGE_KEY, token.trim());
        }
        setDomain("");
        if (data.job_id) {
          router.push(`/research/${data.job_id}`);
        } else {
          setMessage("研究已启动，请稍后刷新查看结果");
          setTimeout(() => fetchJobs(), 3000);
        }
      } else {
        setMessage(res.error || "启动失败");
      }
    } catch {
      setMessage("请求失败");
    } finally {
      setLoading(false);
    }
  };

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

  const statusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-emerald-600 bg-emerald-50";
      case "running":
        return "text-amber-600 bg-amber-50";
      case "failed":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-500 bg-gray-100";
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              研究领域
            </label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="例如：AI法律、跨境电商、独立开发者工具"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !domain.trim()}
            className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "启动中..." : "开始研究"}
          </button>
        </div>

        <button
          type="button"
          onClick={() => setShowToken(!showToken)}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          {showToken ? "隐藏" : "设置"} Admin Token
        </button>
        {showToken && (
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="输入 Admin Token"
            className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-500 focus:border-gray-300 outline-none"
          />
        )}
        {message && <p className="text-sm text-gray-600">{message}</p>}
      </form>

      {jobs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">最近研究</h3>
          <div className="space-y-2">
            {jobs.map((job) => (
              <a
                key={job.id}
                href={`/research/${job.id}`}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3 hover:border-indigo-200 transition-colors"
              >
                <div>
                  <span className="font-medium text-gray-900">
                    {job.domain}
                  </span>
                  <span className="ml-2 text-xs text-gray-400">
                    {job.platforms?.join(", ")}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {job.status === "completed" && (
                    <span className="text-xs text-gray-500">
                      {job.pain_points_extracted} 个需求
                    </span>
                  )}
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(job.status)}`}
                  >
                    {statusLabel(job.status)}
                  </span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
