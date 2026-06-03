const VARIANTS: Record<string, string> = {
  category: "bg-blue-muted text-blue border border-blue/20",
  industry: "bg-purple-soft text-purple-accent border border-purple-accent/20",
  saas: "bg-amber-muted text-amber border border-amber/20",
  plugin: "bg-green-muted text-green border border-green/20",
};

export default function Badge({
  label,
  variant = "category",
}: {
  label: string;
  variant?: string;
}) {
  return (
    <span
      className={`inline-block rounded-md border px-2 py-0.5 text-[11px] font-medium tracking-wide ${
        VARIANTS[variant] || VARIANTS.category
      }`}
    >
      {label}
    </span>
  );
}
