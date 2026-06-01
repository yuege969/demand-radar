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
  // Individual developer feasibility fields
  is_individual_feasible: boolean;
  feasibility_reason: string | null;
  estimated_dev_time: string | null;
  tech_stack_hints: string[] | null;
  market_saturation: string | null;
  individual_score: number;
  opportunity_score: number;
  // Deep analysis enrichment fields
  demand_validation: string | null;
  market_value_analysis: string | null;
  implementation_plan: string | null;
  solo_feasibility: string | null;
  enriched_at: string | null;
}

export interface DemandValidation {
  is_genuine_demand: boolean;
  validation_reasoning: string;
  evidence_from_sources: string;
  frequency_analysis: string;
  user_sentiment_intensity: string;
}

export interface MarketValueAnalysis {
  market_size_estimate: string;
  target_audience: string;
  willingness_to_pay_evidence: string;
  competition_landscape: string;
  monetization_potential: string;
}

export interface ImplementationPlan {
  mvp_scope: string;
  technical_approach: string;
  recommended_tech_stack: string[];
  tech_stack_rationale: string;
  go_to_market_strategy: string;
  monetization_model: string;
}

export interface SoloFeasibility {
  specific_barriers: string;
  how_to_overcome: string;
  realistic_dev_time: string;
  dev_time_reasoning: string;
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

export interface SourceRef {
  platform?: string;
  title?: string;
  url?: string;
  id?: number;
  subreddit?: string;
  score?: number;
  num_comments?: number;
  created_utc?: string;
}

export interface PainPointDetail extends PainPoint {
  score_breakdown: PainScoreBreakdown | null;
  source_posts: SourceRef[];
  related: PainPoint[];
}

export interface Post {
  id: number;
  external_id: string;
  source: string;
  title: string;
  body: string | null;
  url: string | null;
  subreddit: string;
  author: string | null;
  score: number;
  num_comments: number;
  signal_score: number | null;
  analysis_stage: string;
  created_utc: string;
  fetched_at: string;
  processed: number;
}

export interface ResearchJob {
  id: number;
  domain: string;
  platforms: string[];
  status: string;
  total_findings: number;
  pain_points_extracted: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
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

export async function getCategories(): Promise<ApiResponse<{ categories: string[]; industries: string[] }>> {
  return fetchApi("/pain-points/categories/list");
}

export async function searchAll(q: string, params?: Record<string, string>): Promise<ApiResponse<unknown[]>> {
  return fetchApi("/pain-points/search/all", { q, ...params });
}

export async function getPosts(params?: Record<string, string>): Promise<ApiResponse<Post[]>> {
  return fetchApi<Post[]>("/posts", params);
}

export async function getResearchJobs(params?: Record<string, string>): Promise<ApiResponse<ResearchJob[]>> {
  return fetchApi<ResearchJob[]>("/research", params);
}

export async function getResearchJob(id: number): Promise<ApiResponse<ResearchJob>> {
  return fetchApi<ResearchJob>(`/research/${id}`);
}

export async function getResearchPainPoints(id: number, params?: Record<string, string>): Promise<ApiResponse<PainPoint[]>> {
  return fetchApi<PainPoint[]>(`/research/${id}/pain-points`, params);
}

export async function triggerResearch(domain: string, adminToken: string, platforms?: string[]): Promise<ApiResponse<unknown>> {
  const url = `${API_URL}/research`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify({ domain, platforms: platforms || ["web"] }),
  });
  if (!res.ok) {
    return { success: false, data: null, error: `HTTP ${res.status}`, meta: null };
  }
  return res.json();
}
