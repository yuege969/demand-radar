"use client";

import { useEffect, useState } from "react";
import { getPainPoints, getDailyReport } from "@/lib/api";

interface Stats {
  total: number;
  today: number;
}

export default function StatsOverview() {
  const [stats, setStats] = useState<Stats>({ total: 0, today: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getPainPoints({ per_page: "1" }),
      getDailyReport(),
    ]).then(([ppRes, reportRes]) => {
      const total = (ppRes.meta?.total as number) ?? 0;
      const today =
        reportRes.success && reportRes.data
          ? ((reportRes.data.stats?.new_pain_points as number) ?? 0)
          : 0;
      setStats({ total, today });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const cards = [
    { label: "今日新增", value: loading ? "—" : String(stats.today), color: "text-indigo-600" },
    { label: "累计需求", value: loading ? "—" : String(stats.total), color: "text-emerald-600" },
    { label: "SaaS 机会", value: "—", color: "text-amber-600" },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl border border-gray-200 bg-white p-5">
          <p className="text-sm text-gray-500">{c.label}</p>
          <p className={`text-3xl font-bold mt-1 ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}
