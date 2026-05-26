const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  meta: Record<string, unknown> | null;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface PainPoint {
  id: number;
  title: string;
  summary: string;
  category: string | null;
  industry: string | null;
  pain_score: number;
  keywords: string | null;
  source_post_ids: string | null;
  is_saas_idea: boolean;
  is_plugin_idea: boolean;
  business_angle: string | null;
  source_count: number;
  created_at: string;
  updated_at: string;
}

export interface PainScoreBreakdown {
  emotion_intensity: number;
  comment_volume: number;
  repeat_frequency: number;
  involves_money: number;
  has_paid_solution: number;
  automation_difficulty: number;
  is_long_term: number;
  total_score: number;
}

export interface PainPointDetail extends PainPoint {
  score_breakdown: PainScoreBreakdown | null;
  source_posts: Post[];
  related: PainPoint[];
}

export interface Post {
  id: number;
  reddit_id: string;
  title: string;
  body: string | null;
  url: string | null;
  subreddit: string;
  author: string | null;
  score: number;
  num_comments: number;
  created_utc: string;
  fetched_at: string;
  processed: number;
}

export interface ReportSummary {
  report_date: string;
  summary: string;
  top_pains: { id: number; title: string; pain_score: number }[];
  new_pains: { id: number; title: string; pain_score: number }[];
  stats: Record<string, unknown>;
}

export interface TrendPoint {
  date: string;
  total_posts_crawled: number;
  new_pain_points: number;
}

async function fetchApi<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
  const url = new URL(`${API_URL}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    return { success: false, data: null, error: `HTTP ${res.status}`, meta: null };
  }
  return res.json();
}

export async function getPainPoints(params?: Record<string, string>): Promise<ApiResponse<PainPoint[]>> {
  return fetchApi<PainPoint[]>("/pain-points", params);
}

export async function getPainPoint(id: number): Promise<ApiResponse<PainPointDetail>> {
  return fetchApi<PainPointDetail>(`/pain-points/${id}`);
}

export async function getDailyReport(date?: string): Promise<ApiResponse<ReportSummary>> {
  return fetchApi<ReportSummary>("/daily-report", date ? { date } : undefined);
}

export async function getTrends(days?: number, category?: string): Promise<ApiResponse<TrendPoint[]>> {
  return fetchApi<TrendPoint[]>("/trends", { days: String(days || 7), ...(category ? { category } : {}) });
}

export async function getCategories(): Promise<ApiResponse<{ categories: string[]; industries: string[] }>> {
  return fetchApi("/pain-points/categories/list");
}

export async function searchAll(q: string, params?: Record<string, string>): Promise<ApiResponse<unknown[]>> {
  return fetchApi("/pain-points/search/all", { q, ...params });
}

export async function getPosts(params?: Record<string, string>): Promise<ApiResponse<Post[]>> {
  return fetchApi<Post[]>("/posts", params);
}

export async function getCrawlStatus(): Promise<ApiResponse<{ is_running: boolean; last_run_at: string | null; last_result: string | null }>> {
  return fetchApi("/crawl/status");
}
