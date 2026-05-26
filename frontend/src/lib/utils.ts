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

export function scoreColor(score: number): string {
  if (score >= 7) return "text-red-500";
  if (score >= 5) return "text-orange-500";
  if (score >= 3) return "text-yellow-500";
  return "text-green-500";
}

export function scoreBgColor(score: number): string {
  if (score >= 7) return "bg-red-50 border-red-200";
  if (score >= 5) return "bg-orange-50 border-orange-200";
  if (score >= 3) return "bg-yellow-50 border-yellow-200";
  return "bg-green-50 border-green-200";
}
