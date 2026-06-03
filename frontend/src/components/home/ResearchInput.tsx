"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { triggerResearch, getResearchJobs, type ResearchJob } from "@/lib/api";

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
    if (res.success && res.data) setJobs(res.data);
  }, []);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain.trim()) return;
    setLoading(true);
    setMessage("");

    try {
      const res = await triggerResearch(domain.trim(), token.trim());
      if (res.success && res.data) {
        const data = res.data as { job_id?: number };
        if (token.trim()) localStorage.setItem(TOKEN_STORAGE_KEY, token.trim());
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

  const statusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-green bg-green-muted";
      case "running": return "text-amber bg-amber-muted";
      case "failed": return "text-red bg-red-muted";
      default: return "text-text-muted bg-surface-2";
    }
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "completed": return "已完成";
      case "running": return "运行中";
      case "failed": return "失败";
      default: return "等待中";
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-[13px] font-medium text-text-secondary mb-1">研究领域</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="例如：AI法律、跨境电商、独立开发者工具"
              data-research-input
              className="w-full rounded-lg border border-hairline bg-surface-1 px-4 py-2.5 text-[14px] text-text-primary placeholder:text-text-muted focus:border-accent/40 focus:ring-1 focus:ring-accent/40 outline-none transition-colors"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !domain.trim()}
            className="px-5 py-2.5 bg-accent text-white text-[13px] font-medium rounded-lg hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "启动中..." : "开始研究"}
          </button>
        </div>

        <button
          type="button"
          onClick={() => setShowToken(!showToken)}
          className="text-[11px] text-text-muted hover:text-text-secondary transition-colors"
        >
          {showToken ? "隐藏" : "设置"} Admin Token
        </button>
        {showToken && (
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="输入 Admin Token"
            className="w-full rounded-lg border border-hairline bg-surface-1 px-3 py-1.5 text-[12px] text-text-secondary placeholder:text-text-muted focus:border-hairline outline-none"
          />
        )}
        {message && <p className="text-[13px] text-text-secondary">{message}</p>}
      </form>

      {jobs.length > 0 && (
        <div>
          <h3 className="text-[13px] font-medium text-text-muted mb-2">最近研究</h3>
          <div className="space-y-2">
            {jobs.map((job) => (
              <a
                key={job.id}
                href={`/research/${job.id}`}
                className="flex items-center justify-between rounded-lg border border-hairline bg-surface-1 px-4 py-3 hover:border-white/10 transition-colors"
              >
                <div>
                  <span className="text-[14px] font-medium text-text-primary">{job.domain}</span>
                  <span className="ml-2 text-[11px] text-text-muted">{job.platforms?.join(", ")}</span>
                </div>
                <div className="flex items-center gap-3">
                  {job.status === "completed" && (
                    <span className="text-[11px] text-text-muted">{job.pain_points_extracted} 个需求</span>
                  )}
                  <span className={`text-[11px] px-2 py-0.5 rounded-md font-medium ${statusColor(job.status)}`}>
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
