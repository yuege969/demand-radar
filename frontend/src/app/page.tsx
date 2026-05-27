import PainCard from "@/components/ui/PainCard";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface PainPoint {
  id: number;
  title: string;
  summary: string;
  category: string | null;
  industry: string | null;
  pain_score: number;
  is_saas_idea: boolean;
  is_plugin_idea: boolean;
  source_count: number;
}

async function fetchFromAPI<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const [ppResult, reportResult] = await Promise.all([
    fetchFromAPI<{ data: PainPoint[] }>(
      "/pain-points?per_page=10&sort_by=pain_score"
    ),
    fetchFromAPI<{ data: { stats: { new_pain_points: number } } }>(
      "/daily-report"
    ),
  ]);

  const painPoints = ppResult?.data ?? [];

  const total = painPoints.length;
  const today =
    reportResult?.data?.stats?.new_pain_points ?? 0;

  const stats = [
    { label: "今日新增", value: String(today), color: "text-indigo-600" },
    { label: "累计需求", value: String(total), color: "text-emerald-600" },
    { label: "SaaS 机会", value: painPoints.filter((p) => p.is_saas_idea).length.toString(), color: "text-amber-600" },
  ];

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-xl border border-gray-200 bg-white p-5"
          >
            <p className="text-sm text-gray-500">{s.label}</p>
            <p className={`text-3xl font-bold mt-1 ${s.color}`}>
              {s.value}
            </p>
          </div>
        ))}
      </div>
      <section>
        <h2 className="text-xl font-semibold mb-4">今日热门需求</h2>
        {painPoints.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">暂无需求数据</p>
            <p className="text-sm mt-2">
              启动后端并触发数据抓取后将在此显示需求分析结果。
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {painPoints.map((pp) => (
              <PainCard key={pp.id} painPoint={pp} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
