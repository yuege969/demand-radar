"use client";

import { useEffect, useState } from "react";
import { getPainVocabulary, type PainVocabularyItem } from "@/lib/api";

const FALLBACK_VOCAB: PainVocabularyItem[] = [
  { category: "情绪表达", words: ["烦死了", "太麻烦了", "崩溃", "受不了", "累死了"] },
  { category: "求推荐", words: ["有没有工具", "有没有软件", "求推荐", "有没有办法"] },
  { category: "重复劳动", words: ["每天都要做", "重复劳动", "手动操作", "浪费时间"] },
  { category: "付费意愿", words: ["愿意付费", "有付费的吗"] },
];

export default function PainVocabulary() {
  const [vocab, setVocab] = useState<PainVocabularyItem[]>(FALLBACK_VOCAB);
  const [collapsed, setCollapsed] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPainVocabulary().then((res) => {
      if (res.success && res.data && res.data.length > 0) setVocab(res.data);
      setLoading(false);
    });
  }, []);

  const handleWordClick = (word: string) => {
    const input = document.querySelector<HTMLInputElement>("[data-research-input]");
    if (input) {
      const current = input.value;
      if (current && !current.includes(word)) input.value = `${current} ${word}`;
      else if (!current) input.value = word;
      input.focus();
    }
  };

  return (
    <section className="rounded-[10px] border border-hairline bg-surface-1 p-4">
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between w-full text-left"
      >
        <div>
          <h2 className="text-[14px] font-semibold text-text-primary">痛点词库</h2>
          <p className="text-[12px] text-text-muted mt-0.5">
            情绪化关键词能比行业词更准确地发现真实需求
          </p>
        </div>
        <svg
          className={`w-4 h-4 text-text-muted transition-transform duration-200 ${collapsed ? "" : "rotate-180"}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {!collapsed && !loading && (
        <div className="mt-4 space-y-3">
          {vocab.map((group) => (
            <div key={group.category}>
              <p className="text-[11px] font-medium text-text-muted mb-1.5">{group.category}</p>
              <div className="flex flex-wrap gap-1.5">
                {group.words.map((w) => (
                  <button
                    key={w}
                    type="button"
                    onClick={() => handleWordClick(w)}
                    className="inline-flex items-center rounded-md bg-amber-muted border border-amber/20 px-2 py-0.5 text-[11px] font-medium text-amber hover:bg-amber/20 transition-colors"
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
            <div key={i} className="h-6 w-14 rounded-md bg-surface-2 animate-pulse" />
          ))}
        </div>
      )}
    </section>
  );
}
