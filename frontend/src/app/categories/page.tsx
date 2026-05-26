"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCategories, getPainPoints, type PainPoint } from "@/lib/api";
import PainCard from "@/components/ui/PainCard";

const CATEGORY_LABELS: Record<string, { name: string; desc: string; color: string }> = {
  automation: { name: "自动化", desc: "重复任务自动化需求", color: "border-blue-300 bg-blue-50" },
  saas: { name: "SaaS", desc: "软件即服务机会", color: "border-indigo-300 bg-indigo-50" },
  tooling: { name: "工具", desc: "开发与效率工具", color: "border-green-300 bg-green-50" },
  mobile: { name: "移动端", desc: "移动应用需求", color: "border-orange-300 bg-orange-50" },
  content: { name: "内容", desc: "内容创作与管理", color: "border-purple-300 bg-purple-50" },
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [painPoints, setPainPoints] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getCategories().then((res) => {
      if (res.success && res.data) setCategories(res.data.categories);
    });
    getPainPoints({ per_page: "50", sort_by: "pain_score" }).then((res) => {
      if (res.success && res.data) setPainPoints(res.data);
      setLoading(false);
    });
  }, []);

  const filtered = activeCategory
    ? painPoints.filter((p) => p.category === activeCategory)
    : painPoints;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">行业分类</h1>

      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setActiveCategory(null)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            !activeCategory ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          全部
        </button>
        {categories.map((cat) => {
          const info = CATEGORY_LABELS[cat] || { name: cat, desc: "", color: "border-gray-300 bg-gray-50" };
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${info.color} ${
                activeCategory === cat ? "ring-2 ring-indigo-400" : ""
              }`}
            >
              {info.name}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((pp) => (
            <PainCard key={pp.id} painPoint={pp} />
          ))}
        </div>
      )}
    </div>
  );
}
