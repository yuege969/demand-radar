"use client";

import { useEffect, useState } from "react";
import { getTaxonomy, type DomainCategory } from "@/lib/api";

const FALLBACK_CATEGORIES: DomainCategory[] = [
  {
    key: "devtools",
    name: "开发者工具",
    description: "开发效率、代码质量和运维自动化",
    keywords: ["Claude Code", "Cursor", "GitHub", "CI/CD", "Docker", "自动化测试"],
  },
  {
    key: "media",
    name: "自媒体",
    description: "内容选题、制作、分发和数据分析",
    keywords: ["小红书", "抖音", "视频号", "B站", "内容创作", "剪辑"],
  },
  {
    key: "education",
    name: "教育",
    description: "备课、教学管理、家校沟通",
    keywords: ["教师", "备课", "教案", "课件", "班主任", "作业批改"],
  },
  {
    key: "ecommerce",
    name: "电商",
    description: "选品、运营、库存和客服",
    keywords: ["亚马逊", "TikTok Shop", "淘宝", "ERP", "选品", "库存管理"],
  },
];

export default function CategoryNav() {
  const [categories, setCategories] = useState<DomainCategory[]>(FALLBACK_CATEGORIES);
  const [loading, setLoading] = useState(true);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);

  useEffect(() => {
    getTaxonomy().then((res) => {
      if (res.success && res.data && res.data.categories.length > 0) {
        setCategories(res.data.categories);
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-5 w-32 rounded bg-gray-200 animate-pulse" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-8 w-20 rounded-full bg-gray-100 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const handleKeywordClick = (kw: string) => {
    setSelectedKeyword(kw);
    const input = document.querySelector<HTMLInputElement>('[data-research-input]');
    if (input) {
      input.value = kw;
      input.focus();
    }
  };

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">热门研究领域</h2>
      <p className="text-sm text-gray-500 mb-4">按行业分类浏览研究方向和关键词</p>
      <div className="grid gap-4 sm:grid-cols-2">
        {categories.map((cat) => (
          <div
            key={cat.key}
            className="rounded-xl border border-gray-200 bg-white p-4"
          >
            <h3 className="font-semibold text-gray-900 text-sm">{cat.name}</h3>
            <p className="text-xs text-gray-500 mt-0.5 mb-3">{cat.description}</p>
            <div className="flex flex-wrap gap-1.5">
              {cat.keywords.slice(0, 8).map((kw) => (
                <button
                  key={kw}
                  type="button"
                  onClick={() => handleKeywordClick(kw)}
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                    selectedKeyword === kw
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-indigo-100 hover:text-indigo-700"
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
