import Link from "next/link";
import type { PainPoint } from "@/lib/api";
import { toDisplayScore } from "@/lib/utils";
import Badge from "./Badge";

function ScoreBadge({ score }: { score: number }) {
  return (
    <span className="font-mono text-lg font-semibold tracking-tight tabular-nums text-amber">
      {score.toFixed(1)}
    </span>
  );
}

function FeasibilityBadge({ painPoint }: { painPoint: PainPoint }) {
  if (painPoint.is_individual_feasible) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-green-muted px-2 py-0.5 text-[11px] font-medium text-green border border-green/20">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        个人可做
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-surface-2 px-2 py-0.5 text-[11px] font-medium text-text-muted">
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
      门槛较高
    </span>
  );
}

function DensityDots({ sourceCount, score }: { sourceCount: number; score: number }) {
  const density = Math.min(sourceCount / 10, 1) * 0.3 + (score / 100) * 0.4 + 0.3;
  const dots = density >= 0.7 ? 5 : density >= 0.55 ? 4 : density >= 0.4 ? 3 : density >= 0.25 ? 2 : 1;

  return (
    <span className="inline-flex items-center gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`block w-1.5 h-1.5 rounded-full ${
            i < dots ? "bg-amber" : "bg-surface-3"
          }`}
        />
      ))}
    </span>
  );
}

function MarketBadge({ saturation }: { saturation: string | null }) {
  if (!saturation) return null;
  const variants: Record<string, string> = {
    green: "bg-blue-muted text-blue border-blue/20",
    amber: "bg-amber-muted text-amber border-amber/20",
    red: "bg-red-muted text-red border-red/20",
  };
  const labels: Record<string, string> = { green: "蓝海", amber: "中等", red: "红海" };
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${
        variants[saturation] || "bg-surface-2 text-text-muted"
      }`}
    >
      {labels[saturation] || saturation}
    </span>
  );
}

export default function PainCard({ painPoint }: { painPoint: PainPoint }) {
  const score = toDisplayScore(painPoint.opportunity_score, painPoint.pain_score);
  const displaySummary = painPoint.snapshot_summary || painPoint.summary;

  return (
    <Link
      href={`/pain-points/${painPoint.id}`}
      className="card-lift group block rounded-[10px] border border-hairline bg-surface-1 p-5"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-semibold text-text-primary leading-snug line-clamp-2 group-hover:text-accent transition-colors">
          {painPoint.title}
        </h3>
        <div className="shrink-0 flex flex-col items-end gap-0.5">
          <ScoreBadge score={score} />
          {painPoint.opportunity_score > 0 && (
            <span className="text-[10px] text-text-muted font-mono">机会分</span>
          )}
        </div>
      </div>

      <p className="mt-2.5 text-[13px] text-text-secondary leading-relaxed line-clamp-3">
        {displaySummary}
      </p>

      {painPoint.snapshot_opportunity && (
        <div className="mt-3 rounded-lg bg-surface-2 border border-hairline p-3">
          <p className="text-[11px] font-semibold text-amber mb-1">产品机会</p>
          <p className="text-[13px] text-text-secondary leading-relaxed line-clamp-2">
            {painPoint.snapshot_opportunity}
          </p>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5 items-center">
        <FeasibilityBadge painPoint={painPoint} />
        {painPoint.market_saturation && <MarketBadge saturation={painPoint.market_saturation} />}
        {painPoint.category && <Badge label={painPoint.category} variant="category" />}
        {painPoint.industry && <Badge label={painPoint.industry} variant="industry" />}
        {painPoint.snapshot_at && (
          <span className="ml-auto text-[11px] text-text-muted font-mono">AI 分析</span>
        )}
        <span className="text-[11px] text-text-muted">{painPoint.source_count} 来源</span>
      </div>

      {(painPoint.source_count > 0 || painPoint.opportunity_score > 0) && (
        <div className="mt-3 flex items-center gap-2 border-t border-hairline pt-3">
          <span className="text-[11px] text-text-muted">机会密度</span>
          <DensityDots sourceCount={painPoint.source_count} score={painPoint.opportunity_score} />
        </div>
      )}
    </Link>
  );
}
