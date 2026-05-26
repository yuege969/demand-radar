"use client";

import { useEffect, useState } from "react";
import { searchAll, type PaginationMeta } from "@/lib/api";

export function useSearch(q: string, page = 1) {
  const [results, setResults] = useState<unknown[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    searchAll(q, { page: String(page), per_page: "20" })
      .then((res) => {
        if (res.success && res.data) {
          setResults(res.data);
          if (res.meta) setMeta(res.meta as unknown as PaginationMeta);
        } else {
          setError(res.error ?? "Search failed");
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Unknown error"))
      .finally(() => setLoading(false));
  }, [q, page]);

  return { results, meta, loading, error };
}
