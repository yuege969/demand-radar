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
  source_urls: string | null;
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
  // Snapshot enrichment (lightweight, auto-generated)
  snapshot_summary: string | null;
  snapshot_opportunity: string | null;
  snapshot_at: string | null;
  // On-demand modular deep analysis (JSON)
  enrichment_data: string | null;
  // Legacy deep analysis fields
  demand_validation: string | null;
  market_value_analysis: string | null;
  implementation_plan: string | null;
  solo_feasibility: string | null;
  enriched_at: string | null;
}

export interface EnrichmentModuleInfo {
  key: string;
  display_name: string;
  description: string;
  completed: boolean;
  output_fields: string[];
}

export interface EnrichmentPillar {
  key: string;
  display_name: string;
  description: string;
  modules: EnrichmentModuleInfo[];
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
  discussion_volume: number;
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
  snippet?: string;
  url?: string;
}

export interface PainPointDetail extends PainPoint {
  score_breakdown: PainScoreBreakdown | null;
  source_findings: SourceRef[];
  related: PainPoint[];
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
  is_enriching: boolean;
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

export async function getResearchJobs(params?: Record<string, string>): Promise<ApiResponse<ResearchJob[]>> {
  return fetchApi<ResearchJob[]>("/research", params);
}

export async function getResearchJob(id: number): Promise<ApiResponse<ResearchJob>> {
  return fetchApi<ResearchJob>(`/research/${id}`);
}

export async function getResearchPainPoints(id: number, params?: Record<string, string>): Promise<ApiResponse<PainPoint[]>> {
  return fetchApi<PainPoint[]>(`/research/${id}/pain-points`, params);
}

export async function reEnrichJob(jobId: number): Promise<ApiResponse<{ message: string; enriched: number }>> {
  const res = await fetch(`${API_URL}/research/${jobId}/re-enrich`, { method: "POST" });
  if (!res.ok) {
    return { success: false, data: null, error: `HTTP ${res.status}`, meta: null };
  }
  return res.json();
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

export async function getEnrichmentModules(painPointId: number): Promise<ApiResponse<EnrichmentPillar[]>> {
  return fetchApi<EnrichmentPillar[]>(`/pain-points/${painPointId}/enrich/modules`);
}

export async function enrichPainPoint(
  painPointId: number,
  modules: string[]
): Promise<ApiResponse<{ message: string; pending: string[]; enriched?: number }>> {
  const res = await fetch(`${API_URL}/pain-points/${painPointId}/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modules }),
  });
  if (!res.ok) {
    return { success: false, data: null, error: `HTTP ${res.status}`, meta: null };
  }
  return res.json();
}
