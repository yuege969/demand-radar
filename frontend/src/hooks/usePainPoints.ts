"use client";

import { useEffect, useState } from "react";
import { getPainPoints, type PainPoint, type PaginationMeta } from "@/lib/api";

interface UsePainPointsOptions {
  page?: number;
  perPage?: number;
  category?: string;
  industry?: string;
  sortBy?: string;
  search?: string;
}

export function usePainPoints(options: UsePainPointsOptions = {}) {
  const [data, setData] = useState<PainPoint[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = {
      page: String(options.page ?? 1),
      per_page: String(options.perPage ?? 20),
    };
    if (options.category) params.category = options.category;
    if (options.industry) params.industry = options.industry;
    if (options.sortBy) params.sort_by = options.sortBy;
    if (options.search) params.search = options.search;

    getPainPoints(params)
      .then((res) => {
        if (res.success && res.data) {
          setData(res.data);
          if (res.meta) setMeta(res.meta as unknown as PaginationMeta);
        } else {
          setError(res.error ?? "Failed to load");
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Unknown error"))
      .finally(() => setLoading(false));
  }, [options.page, options.perPage, options.category, options.industry, options.sortBy, options.search]);

  return { data, meta, loading, error };
}
