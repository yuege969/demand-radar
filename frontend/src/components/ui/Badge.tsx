const VARIANTS: Record<string, string> = {
  category: "bg-blue-50 text-blue-700 border-blue-200",
  industry: "bg-purple-50 text-purple-700 border-purple-200",
  saas: "bg-amber-50 text-amber-700 border-amber-200",
  plugin: "bg-teal-50 text-teal-700 border-teal-200",
};

export default function Badge({ label, variant = "category" }: { label: string; variant?: string }) {
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${VARIANTS[variant] || VARIANTS.category}`}>
      {label}
    </span>
  );
}
