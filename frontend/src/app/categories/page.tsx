"use client";

import { useEffect, useState } from "react";
import { getCategories, getPainPoints, type PainPoint } from "@/lib/api";
import PainCard from "@/components/ui/PainCard";
import ScrollRestoration from "@/components/common/ScrollRestoration";

const CATEGORY_STYLES: Record<string, { name: string; active: string; inactive: string }> = {
  automation: { name: "自动化", active: "bg-blue-muted text-blue border-blue/30", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" },
  saas: { name: "SaaS", active: "bg-accent-muted text-accent border-accent/30", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" },
  tooling: { name: "工具", active: "bg-green-muted text-green border-green/30", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" },
  mobile: { name: "移动端", active: "bg-amber-muted text-amber border-amber/30", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" },
  content: { name: "内容", active: "bg-purple-soft text-purple-accent border-purple-accent/30", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" },
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [painPoints, setPainPoints] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCategories().then((res) => {
      if (res.success && res.data) setCategories(res.data.categories);
    });
    getPainPoints({ per_page: "50", sort_by: "opportunity_score" }).then((res) => {
      if (res.success && res.data) setPainPoints(res.data);
      setLoading(false);
    });
  }, []);

  const filtered = activeCategory
    ? painPoints.filter((p) => p.category === activeCategory)
    : painPoints;

  return (
    <ScrollRestoration>
      <div className="space-y-6">
        <h1 className="text-xl font-semibold text-text-primary tracking-tight">行业分类</h1>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`rounded-md border px-3 py-1.5 text-[13px] font-medium transition-colors ${
              !activeCategory
                ? "bg-gray-900 text-white border-gray-900/80"
                : "bg-surface-2 text-text-secondary border-hairline hover:text-text-primary"
            }`}
          >
            全部
          </button>
          {categories.map((cat) => {
            const style = CATEGORY_STYLES[cat] || { name: cat, active: "bg-surface-2 text-text-primary border-hairline", inactive: "bg-surface-2 text-text-muted border-hairline hover:text-text-primary" };
            const isActive = activeCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`rounded-md border px-3 py-1.5 text-[13px] font-medium transition-colors ${
                  isActive ? style.active : style.inactive
                }`}
              >
                {style.name}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 rounded-[10px] bg-surface-1 animate-pulse" />
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
    </ScrollRestoration>
  );
}
