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
  // High score = warm/amber (good opportunity), low = cool/gray
  if (score >= 70) return "text-amber-600";
  if (score >= 50) return "text-orange-500";
  if (score >= 30) return "text-yellow-600";
  return "text-gray-400";
}

export function scoreBgColor(score: number): string {
  if (score >= 70) return "bg-amber-50 border-amber-200";
  if (score >= 50) return "bg-orange-50 border-orange-200";
  if (score >= 30) return "bg-yellow-50 border-yellow-200";
  return "bg-gray-50 border-gray-200";
}
