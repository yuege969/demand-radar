"use client";

import { useEffect, useState } from "react";
import { getTrends, type TrendPoint } from "@/lib/api";

export default function TrendsPage() {
  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTrends(30).then((res) => {
      if (res.success && res.data) setData(res.data);
      setLoading(false);
    });
  }, []);

  const maxPosts = Math.max(...data.map((d) => d.total_posts_crawled), 1);
  const maxNew = Math.max(...data.map((d) => d.new_pain_points), 1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">需求趋势</h1>

      {loading ? (
        <div className="space-y-4">
          <div className="h-64 rounded-xl bg-gray-100 animate-pulse" />
        </div>
      ) : data.length === 0 ? (
        <p className="text-center py-20 text-gray-400">暂无趋势数据，启动日报生成后将在此显示。</p>
      ) : (
        <div className="space-y-8">
          <section className="rounded-xl border border-gray-200 bg-white p-6">
            <h2 className="font-semibold mb-4">日抓取帖子数</h2>
            <div className="flex items-end gap-1 h-40">
              {data.map((d) => (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">{d.total_posts_crawled}</span>
                  <div
                    className="w-full bg-indigo-400 rounded-t"
                    style={{ height: `${(d.total_posts_crawled / maxPosts) * 100}%`, minHeight: "2px" }}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-400">
              <span>{data[0]?.date?.slice(5)}</span>
              <span>{data[data.length - 1]?.date?.slice(5)}</span>
            </div>
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-6">
            <h2 className="font-semibold mb-4">日新增需求数</h2>
            <div className="flex items-end gap-1 h-40">
              {data.map((d) => (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">{d.new_pain_points}</span>
                  <div
                    className="w-full bg-emerald-400 rounded-t"
                    style={{ height: `${(d.new_pain_points / maxNew) * 100}%`, minHeight: "2px" }}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-400">
              <span>{data[0]?.date?.slice(5)}</span>
              <span>{data[data.length - 1]?.date?.slice(5)}</span>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
