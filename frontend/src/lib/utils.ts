export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}

/** Normalize pain_score (0-10) to the 0-100 display scale when no opportunity_score is available. */
export function toDisplayScore(opportunityScore: number, painScore: number): number {
  return opportunityScore > 0 ? opportunityScore : painScore * 10;
}

export function scoreColor(score: number): string {
  // 0-100 scale: >70 high, >50 medium, >30 low, rest minimal
  if (score >= 70) return "text-red-500";
  if (score >= 50) return "text-orange-500";
  if (score >= 30) return "text-yellow-500";
  return "text-green-500";
}

export function scoreBgColor(score: number): string {
  if (score >= 70) return "bg-red-50 border-red-200";
  if (score >= 50) return "bg-orange-50 border-orange-200";
  if (score >= 30) return "bg-yellow-50 border-yellow-200";
  return "bg-green-50 border-green-200";
}
