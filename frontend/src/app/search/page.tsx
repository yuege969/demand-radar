"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { searchAll, type PainPoint } from "@/lib/api";
import PainCard from "@/components/ui/PainCard";

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get("q") || "";
  const [inputValue, setInputValue] = useState(query);
  const [results, setResults] = useState<PainPoint[]>([]);
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback((q: string) => {
    if (!q.trim()) { setResults([]); return; }
    setLoading(true);
    searchAll(q, { per_page: "20" })
      .then((res) => {
        if (res.success && res.data) {
          setResults(res.data as unknown as PainPoint[]);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (query) { setInputValue(query); doSearch(query); }
  }, [query, doSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      router.push(`/search?q=${encodeURIComponent(inputValue.trim())}`);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="搜索需求、关键词、行业..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
        <button type="submit" className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 transition-colors">
          搜索
        </button>
      </form>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-40 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      ) : query ? (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            搜索 &quot;{query}&quot; — {results.length} 个结果
          </p>
          {results.length === 0 ? (
            <p className="text-center py-12 text-gray-400">未找到相关需求</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {results.map((p) => (
                <PainCard key={p.id} painPoint={p} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <p className="text-center py-20 text-gray-400">输入关键词搜索需求</p>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="max-w-3xl mx-auto"><div className="h-64 rounded-xl bg-gray-100 animate-pulse" /></div>}>
      <SearchContent />
    </Suspense>
  );
}
