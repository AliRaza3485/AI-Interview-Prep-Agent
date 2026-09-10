import type { GapAnalysis } from "@/lib/types";

interface GapAnalysisPreviewProps {
  gapAnalysis: GapAnalysis;
}

function List({ items, tone }: { items: string[]; tone: "sage" | "clay" | "paper" }) {
  const dotColor =
    tone === "sage" ? "bg-sage" : tone === "clay" ? "bg-clay" : "bg-paper-300";

  if (items.length === 0) {
    return <p className="text-sm text-paper-300/70">None identified.</p>;
  }

  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-3 text-sm text-paper-100">
          <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dotColor}`} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function GapAnalysisPreview({ gapAnalysis }: GapAnalysisPreviewProps) {
  return (
    <div className="animate-cross-fade rounded-sm border border-ink-600 bg-ink-800 p-6 sm:p-8">
      <h2 className="font-serif text-xl text-paper-100">
        Here&apos;s what stood out
      </h2>
      <p className="mt-2 text-sm text-paper-300">
        This is what the interview will focus on — questions are built from your gaps
        and focus areas, not a generic bank.
      </p>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div>
          <h3 className="mb-3 text-sm font-medium text-sage">Strengths</h3>
          <List items={gapAnalysis.strengths} tone="sage" />
        </div>
        <div>
          <h3 className="mb-3 text-sm font-medium text-clay">Gaps</h3>
          <List items={gapAnalysis.gaps} tone="clay" />
        </div>
        <div>
          <h3 className="mb-3 text-sm font-medium text-paper-300">
            Worth a closer look
          </h3>
          <List items={gapAnalysis.partial_matches} tone="paper" />
        </div>
        <div>
          <h3 className="mb-3 text-sm font-medium text-paper-300">
            Interview will probe
          </h3>
          <List items={gapAnalysis.focus_areas} tone="paper" />
        </div>
      </div>
    </div>
  );
}
