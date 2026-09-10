import type { CategoryBreakdownEntry } from "@/lib/types";

interface CategoryBreakdownChartProps {
  breakdown: Record<string, CategoryBreakdownEntry>;
}

const CATEGORY_LABEL: Record<string, string> = {
  technical: "Technical",
  behavioral: "Behavioral",
  project_deep_dive: "Project deep dive",
};

export default function CategoryBreakdownChart({
  breakdown,
}: CategoryBreakdownChartProps) {
  const entries = Object.entries(breakdown);

  if (entries.length === 0) return null;

  return (
    <div className="rounded-sm border border-ink-600 bg-ink-800 p-6 sm:p-8">
      <h3 className="font-serif text-lg text-paper-100">By category</h3>
      <div className="mt-6 space-y-5">
        {entries.map(([category, data]) => (
          <div key={category}>
            <div className="mb-1.5 flex items-baseline justify-between text-sm">
              <span className="text-paper-100">
                {CATEGORY_LABEL[category] ?? category}
              </span>
              <span className="font-mono text-paper-300">
                {data.average_score.toFixed(1)} · {data.questions_count}{" "}
                {data.questions_count === 1 ? "question" : "questions"}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-ink-700">
              <div
                className="h-full rounded-full bg-amber"
                style={{ width: `${(data.average_score / 10) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
