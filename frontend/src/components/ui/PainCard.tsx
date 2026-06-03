import Link from "next/link";
import type { PainPoint } from "@/lib/api";
import { scoreBgColor, toDisplayScore } from "@/lib/utils";
import Badge from "./Badge";

function FeasibilityBadge({ painPoint }: { painPoint: PainPoint }) {
  if (painPoint.is_individual_feasible) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        个人可做
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
      门槛较高
    </span>
  );
}

function DensityStars({ sourceCount, opportunityScore }: { sourceCount: number; opportunityScore: number }) {
  const density = Math.min(sourceCount / 10, 1) * 0.3 + (opportunityScore / 100) * 0.4 + 0.3;
  const stars = density >= 0.7 ? 5 : density >= 0.55 ? 4 : density >= 0.4 ? 3 : density >= 0.25 ? 2 : 1;

  return (
    <span className="inline-flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg
          key={i}
          className={`w-3 h-3 ${i < stars ? "text-amber-400" : "text-gray-200"}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </span>
  );
}

function MarketBadge({ saturation }: { saturation: string | null }) {
  if (!saturation) return null;
  const colors = {
    green: "bg-blue-100 text-blue-700",
    amber: "bg-yellow-100 text-yellow-700",
    red: "bg-red-100 text-red-700",
  };
  const labels = { green: "蓝海", amber: "中等", red: "红海" };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[saturation as keyof typeof colors] || "bg-gray-100 text-gray-600"}`}>
      {labels[saturation as keyof typeof labels] || saturation}
    </span>
  );
}

export default function PainCard({ painPoint }: { painPoint: PainPoint }) {
  const displaySummary = painPoint.snapshot_summary || painPoint.summary;

  return (
    <Link
      href={`/pain-points/${painPoint.id}`}
      className={`block rounded-xl border p-5 transition-all hover:shadow-md ${scoreBgColor(toDisplayScore(painPoint.opportunity_score, painPoint.pain_score))}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 line-clamp-2">{painPoint.title}</h3>
        <div className="shrink-0 flex flex-col items-end gap-1">
          <span className="rounded-full bg-white px-2.5 py-0.5 text-sm font-bold text-gray-700 shadow-sm">
            {toDisplayScore(painPoint.opportunity_score, painPoint.pain_score).toFixed(1)}
          </span>
          {painPoint.opportunity_score > 0 && (
            <span className="text-xs text-gray-400">机会分</span>
          )}
        </div>
      </div>

      <p className="mt-2 text-sm text-gray-700 line-clamp-3 leading-relaxed">{displaySummary}</p>

      {painPoint.snapshot_opportunity && (
        <div className="mt-3 rounded-lg bg-white/60 border border-gray-100 p-3">
          <p className="text-xs font-medium text-amber-700 mb-1">产品机会</p>
          <p className="text-sm text-amber-800 line-clamp-2">{painPoint.snapshot_opportunity}</p>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        <FeasibilityBadge painPoint={painPoint} />
        {painPoint.market_saturation && <MarketBadge saturation={painPoint.market_saturation} />}
        {painPoint.category && <Badge label={painPoint.category} variant="category" />}
        {painPoint.industry && <Badge label={painPoint.industry} variant="industry" />}
        {painPoint.snapshot_at && (
          <span className="ml-auto text-xs text-gray-400">AI 分析</span>
        )}
        <span className="text-xs text-gray-400">{painPoint.source_count} 来源</span>
      </div>

      {(painPoint.source_count > 0 || painPoint.opportunity_score > 0) && (
        <div className="mt-3 flex items-center gap-1.5 border-t border-gray-100 pt-3">
          <span className="text-xs text-gray-400">机会密度</span>
          <DensityStars sourceCount={painPoint.source_count} opportunityScore={painPoint.opportunity_score} />
        </div>
      )}
    </Link>
  );
}
