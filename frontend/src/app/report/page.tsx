"use client";

import { useEffect, useState } from "react";
import { getDailyReport, type ReportSummary } from "@/lib/api";
import { formatScore } from "@/lib/utils";

export default function DailyReportPage() {
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDailyReport().then((res) => {
      if (res.success && res.data) setReport(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-gray-200" />
        <div className="h-64 rounded-xl bg-gray-100" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-20 space-y-2">
        <p className="text-lg text-gray-500">暂无日报</p>
        <p className="text-sm text-gray-400">日报每日 08:00 自动生成，或手动触发数据抓取后生成。</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">日报 — {report.report_date}</h1>

      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="font-semibold text-gray-900 mb-3">AI 摘要</h2>
        <p className="text-gray-700 leading-relaxed">{report.summary}</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        {Object.entries(report.stats).map(([k, v]) => (
          <div key={k} className="rounded-xl border border-gray-200 bg-white p-4 text-center">
            <p className="text-sm text-gray-500">{k}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{String(v)}</p>
          </div>
        ))}
      </div>

      {report.top_pains.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">TOP 需求</h2>
          <div className="space-y-2">
            {report.top_pains.map((p, i) => (
              <div key={p.id} className="flex items-center gap-3 rounded-lg border border-gray-100 p-3">
                <span className="text-sm font-bold text-gray-400 w-6">#{i + 1}</span>
                <span className="flex-1 text-sm text-gray-900">{p.title}</span>
                <span className="text-sm font-bold text-orange-600">{formatScore(p.pain_score)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {report.new_pains.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="font-semibold text-gray-900 mb-4">新发现需求</h2>
          <div className="space-y-2">
            {report.new_pains.map((p) => (
              <div key={p.id} className="flex items-center gap-3 rounded-lg border border-green-100 bg-green-50 p-3">
                <span className="flex-1 text-sm text-gray-900">{p.title}</span>
                <span className="text-sm font-bold text-green-700">{formatScore(p.pain_score)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
