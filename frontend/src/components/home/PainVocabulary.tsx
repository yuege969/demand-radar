"use client";

import { useEffect, useState } from "react";
import { getPainVocabulary, type PainVocabularyItem } from "@/lib/api";

const FALLBACK_VOCAB: PainVocabularyItem[] = [
  {
    category: "情绪表达",
    words: ["烦死了", "太麻烦了", "崩溃", "受不了", "累死了"],
  },
  {
    category: "求推荐",
    words: ["有没有工具", "有没有软件", "求推荐", "有没有办法"],
  },
  {
    category: "重复劳动",
    words: ["每天都要做", "重复劳动", "手动操作", "浪费时间"],
  },
  {
    category: "付费意愿",
    words: ["愿意付费", "有付费的吗"],
  },
];

export default function PainVocabulary() {
  const [vocab, setVocab] = useState<PainVocabularyItem[]>(FALLBACK_VOCAB);
  const [collapsed, setCollapsed] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPainVocabulary().then((res) => {
      if (res.success && res.data && res.data.length > 0) {
        setVocab(res.data);
      }
      setLoading(false);
    });
  }, []);

  const handleWordClick = (word: string) => {
    const input = document.querySelector<HTMLInputElement>('[data-research-input]');
    if (input) {
      const current = input.value;
      if (current && !current.includes(word)) {
        input.value = `${current} ${word}`;
      } else if (!current) {
        input.value = word;
      }
      input.focus();
    }
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between w-full text-left"
      >
        <div>
          <h2 className="text-sm font-semibold text-gray-900">痛点词库</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            情绪化关键词能比行业词更准确地发现真实需求
          </p>
        </div>
        <span className={`text-gray-400 transition-transform ${collapsed ? "" : "rotate-180"}`}>
          ▼
        </span>
      </button>

      {!collapsed && !loading && (
        <div className="mt-4 space-y-3">
          {vocab.map((group) => (
            <div key={group.category}>
              <p className="text-xs font-medium text-gray-400 mb-1.5">{group.category}</p>
              <div className="flex flex-wrap gap-1.5">
                {group.words.map((w) => (
                  <button
                    key={w}
                    type="button"
                    onClick={() => handleWordClick(w)}
                    className="inline-flex items-center rounded-full bg-orange-50 border border-orange-200 px-2.5 py-0.5 text-xs font-medium text-orange-700 hover:bg-orange-100 transition-colors"
                  >
                    {w}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!collapsed && loading && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-7 w-16 rounded-full bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}
    </section>
  );
}
