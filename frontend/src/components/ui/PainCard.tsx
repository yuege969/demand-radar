import Link from "next/link";
import type { PainPoint } from "@/lib/api";
import { scoreBgColor } from "@/lib/utils";
import Badge from "./Badge";

export default function PainCard({ painPoint }: { painPoint: PainPoint }) {
  return (
    <Link
      href={`/pain-points/${painPoint.id}`}
      className={`block rounded-xl border p-5 transition-all hover:shadow-md ${scoreBgColor(painPoint.pain_score)}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 line-clamp-2">{painPoint.title}</h3>
        <span className="shrink-0 rounded-full bg-white px-2.5 py-0.5 text-sm font-bold text-gray-700 shadow-sm">
          {painPoint.pain_score.toFixed(1)}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-600 line-clamp-3">{painPoint.summary}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
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
