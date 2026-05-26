"use client";

import { useEffect, useState } from "react";
import { getPainPoints, type PainPoint } from "@/lib/api";
import StatsOverview from "@/components/home/StatsOverview";
import PainCard from "@/components/ui/PainCard";

export default function HomePage() {
  const [painPoints, setPainPoints] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPainPoints({ per_page: "10", sort_by: "pain_score" }).then((res) => {
      if (res.success && res.data) setPainPoints(res.data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-8">
      <StatsOverview />

      <section>
        <h2 className="text-xl font-semibold mb-4">今日热门需求</h2>
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 rounded-xl bg-gray-100 animate-pulse" />
            ))}
          </div>
        ) : painPoints.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">暂无需求数据</p>
            <p className="text-sm mt-2">启动后端并触发数据抓取后将在此显示需求分析结果。</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {painPoints.map((pp) => (
              <PainCard key={pp.id} painPoint={pp} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
