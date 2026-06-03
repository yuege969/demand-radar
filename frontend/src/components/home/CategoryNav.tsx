"use client";

import { useEffect, useState } from "react";
import { getTaxonomy, type DomainCategory } from "@/lib/api";

const FALLBACK_CATEGORIES: DomainCategory[] = [
  { key: "devtools", name: "开发者工具", description: "开发效率、代码质量和运维自动化", keywords: ["Claude Code", "Cursor", "GitHub", "CI/CD", "Docker", "自动化测试"] },
  { key: "media", name: "自媒体", description: "内容选题、制作、分发和数据分析", keywords: ["小红书", "抖音", "视频号", "B站", "内容创作", "剪辑"] },
  { key: "education", name: "教育", description: "备课、教学管理、家校沟通", keywords: ["教师", "备课", "教案", "课件", "班主任", "作业批改"] },
  { key: "ecommerce", name: "电商", description: "选品、运营、库存和客服", keywords: ["亚马逊", "TikTok Shop", "淘宝", "ERP", "选品", "库存管理"] },
];

export default function CategoryNav() {
  const [categories, setCategories] = useState<DomainCategory[]>(FALLBACK_CATEGORIES);
  const [loading, setLoading] = useState(true);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);

  useEffect(() => {
    getTaxonomy().then((res) => {
      if (res.success && res.data && res.data.categories.length > 0) setCategories(res.data.categories);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <section className="space-y-3">
        <div className="h-5 w-32 rounded bg-surface-2 animate-pulse" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-7 w-16 rounded-md bg-surface-1 animate-pulse" />
          ))}
        </div>
      </section>
    );
  }

  const handleKeywordClick = (kw: string) => {
    setSelectedKeyword(kw);
    const input = document.querySelector<HTMLInputElement>("[data-research-input]");
    if (input) { input.value = kw; input.focus(); }
  };

  return (
    <section>
      <h2 className="text-[15px] font-semibold text-text-primary mb-1">热门研究领域</h2>
      <p className="text-[13px] text-text-secondary mb-4">按行业分类浏览研究方向和关键词</p>
      <div className="grid gap-4 sm:grid-cols-2">
        {categories.map((cat) => (
          <div key={cat.key} className="rounded-[10px] border border-hairline bg-surface-1 p-4">
            <h3 className="text-[14px] font-semibold text-text-primary">{cat.name}</h3>
            <p className="text-[12px] text-text-muted mt-0.5 mb-3">{cat.description}</p>
            <div className="flex flex-wrap gap-1.5">
              {cat.keywords.slice(0, 8).map((kw) => (
                <button
                  key={kw}
                  type="button"
                  onClick={() => handleKeywordClick(kw)}
                  className={`rounded-md px-2 py-0.5 text-[11px] font-medium font-mono transition-colors ${
                    selectedKeyword === kw
                      ? "bg-accent text-white"
                      : "bg-surface-2 text-text-secondary hover:text-text-primary hover:bg-surface-3"
                  }`}
                >
                  {kw}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
