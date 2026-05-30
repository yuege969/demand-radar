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
      <p className="mt-2 text-sm text-gray-600 line-clamp-3">{painPoint.summary}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <FeasibilityBadge painPoint={painPoint} />
        {painPoint.estimated_dev_time && (
          <span className="inline-flex items-center rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
            {painPoint.estimated_dev_time}
          </span>
        )}
        {painPoint.market_saturation && <MarketBadge saturation={painPoint.market_saturation} />}
        {painPoint.category && <Badge label={painPoint.category} variant="category" />}
        {painPoint.industry && <Badge label={painPoint.industry} variant="industry" />}
        {painPoint.is_saas_idea && <Badge label="SaaS" variant="saas" />}
        {painPoint.is_plugin_idea && <Badge label="插件" variant="plugin" />}
        <span className="ml-auto text-xs text-gray-400">
          {painPoint.source_count} 来源
        </span>
      </div>
    </Link>
  );
}
