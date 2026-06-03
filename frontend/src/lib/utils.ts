export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit",
  });
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}

export function toDisplayScore(opportunityScore: number, painScore: number): number {
  return opportunityScore > 0 ? opportunityScore : painScore * 10;
}

export function scoreColor(score: number): string {
  if (score >= 70) return "text-amber";
  if (score >= 50) return "text-amber/80";
  if (score >= 30) return "text-amber/60";
  return "text-text-muted";
}

export function scoreBgColor(score: number): string {
  if (score >= 70) return "bg-amber-muted border-amber/20";
  if (score >= 50) return "bg-amber-muted/50 border-amber/10";
  if (score >= 30) return "bg-surface-2 border-hairline";
  return "bg-surface-1 border-hairline";
}
