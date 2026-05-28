"use client";

import { useState, useEffect, useCallback } from "react";
import { triggerCrawl, getCrawlStatus, type StepStatus } from "@/lib/api";

const STEP_LABELS: Record<string, string> = {
  crawl_reddit: "Reddit 抓取",
  crawl_hn: "HN 抓取",
  analyze: "AI 分析",
  report: "日报生成",
};

const STATUS_ICON: Record<string, string> = {
  pending: "○",
  running: "◌",
  completed: "✓",
  failed: "✗",
  skipped: "—",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-400",
  running: "text-blue-600",
  completed: "text-emerald-600",
  failed: "text-red-600",
  skipped: "text-gray-300",
};

function formatTime(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function stepSummary(step: StepStatus): string | null {
  if (step.status === "failed") return step.error || "未知错误";
  if (step.status !== "completed" || !step.result) return null;
  const r = step.result;
  switch (step.step) {
    case "crawl_reddit":
      return `抓取 ${r.posts_fetched ?? "?"} 条帖子`;
    case "crawl_hn":
      return `抓取 ${r.posts_fetched ?? "?"} 条帖子`;
    case "analyze":
      return `处理 ${r.processed ?? "?"} 条，发现 ${r.new_pain_points ?? "?"} 个新痛点`;
    case "report":
      return `报告日期 ${r.report_date ?? "?"}，共 ${r.total ?? "?"} 个痛点`;
    default:
      return null;
  }
}

export default function TriggerPanel() {
  const [token, setToken] = useState("");
  const [steps, setSteps] = useState<StepStatus[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [modelReady, setModelReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  const fetchStatus = useCallback(async () => {
    const res = await getCrawlStatus();
    if (res.success && res.data) {
      setIsRunning(res.data.is_running);
      setSteps(res.data.steps ?? []);
      setModelReady(res.data.model_ready);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleTrigger = async (startStep?: string) => {
    if (!token.trim()) {
      setError("请输入 Admin Token");
      return;
    }
    setError(null);
    try {
      const res = await triggerCrawl(token.trim(), startStep);
      if (!res.success) {
        setError(res.error ?? "触发失败");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "网络请求失败");
    }
    fetchStatus();
  };

  const runningStep = steps.find((s) => s.status === "running");
  const currentStep = runningStep
    ? STEP_LABELS[runningStep.step] || runningStep.label
    : null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-gray-700 w-full text-left"
      >
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        流程控制
        {isRunning && currentStep && (
          <span className="text-xs text-blue-600 ml-2">
            {currentStep} 执行中...
          </span>
        )}
        {!isRunning && steps.length > 0 && (
          <span className="text-xs text-gray-400 ml-auto">
            {steps.every((s) => s.status === "completed") ? "全部完成" : "就绪"}
          </span>
        )}
        {steps.length === 0 && (
          <span className="text-xs text-gray-400 ml-auto">未初始化</span>
        )}
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border text-sm">
            <span className="text-gray-600">模型状态</span>
            <span
              className={`inline-flex items-center gap-1 text-xs font-medium ${
                modelReady ? "text-emerald-700" : "text-amber-700"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  modelReady ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {modelReady ? "Embedding 模型就绪" : "模型加载中..."}
            </span>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Admin Token</label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="输入 ADMIN_API_TOKEN"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {steps.length > 0 && (
            <div className="space-y-1.5">
              {steps.map((step, i) => {
                const isRunnable = step.status === "completed" || step.status === "failed";
                const nextStep = step.step;
                return (
                  <div
                    key={step.step}
                    className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                      step.status === "running"
                        ? "border-blue-200 bg-blue-50"
                        : step.status === "failed"
                          ? "border-red-200 bg-red-50"
                          : "border-gray-100 bg-gray-50"
                    }`}
                  >
                    <span className="text-xs text-gray-400 w-5">{i + 1}</span>
                    <span className={`text-base ${STATUS_COLOR[step.status] ?? "text-gray-400"}`}>
                      {STATUS_ICON[step.status] ?? "○"}
                    </span>
                    <span className="flex-1 text-gray-700">
                      {STEP_LABELS[step.step] || step.label}
                      {step.status === "running" && step.message && (
                        <span className="ml-2 text-xs text-blue-500 font-normal">{step.message}</span>
                      )}
                    </span>
                    {step.started_at && (
                      <span className="text-xs text-gray-400">
                        {formatTime(step.started_at)}
                      </span>
                    )}
                    {step.status === "running" && (
                      <span className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    )}
                    {isRunnable && (
                      <button
                        onClick={() => handleTrigger(nextStep)}
                        disabled={isRunning || (step.step === "analyze" && !modelReady)}
                        className="text-xs px-2 py-0.5 rounded border border-gray-300 bg-white text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                      >
                        {step.status === "failed" ? "重试" : "从此执行"}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {steps.length > 0 && (
            <div className="text-xs text-gray-400 space-y-0.5">
              {steps.map((step) => {
                const summary = stepSummary(step);
                if (!summary) return null;
                return (
                  <div key={step.step}>
                    <span className={STATUS_COLOR[step.status]}>{STATUS_ICON[step.status]}</span>{" "}
                    {STEP_LABELS[step.step]}: {summary}
                  </div>
                );
              })}
            </div>
          )}

          <button
            onClick={() => handleTrigger()}
            disabled={isRunning || !modelReady}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {!modelReady ? (
              "等待模型加载..."
            ) : isRunning ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                执行中...
              </span>
            ) : (
              "触发完整流程"
            )}
          </button>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>
      )}
    </div>
  );
}
