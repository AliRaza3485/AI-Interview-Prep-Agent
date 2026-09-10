interface ReportSummaryProps {
  overallScore: number;
  readinessLevel: string;
  recommendationSummary: string;
}

function readinessTone(level: string): string {
  const normalized = level.toLowerCase();
  if (normalized.includes("ready for real")) return "text-sage";
  if (normalized.includes("almost")) return "text-amber";
  return "text-clay";
}

export default function ReportSummary({
  overallScore,
  readinessLevel,
  recommendationSummary,
}: ReportSummaryProps) {
  return (
    <div className="rounded-sm border border-ink-600 bg-ink-800 p-6">
      <p className="text-sm text-paper-300">Overall score</p>
      <p className="mt-1 font-serif text-6xl text-paper-100">
        {overallScore.toFixed(1)}
        <span className="text-2xl text-paper-300">/10</span>
      </p>
      <p className={`mt-3 text-sm font-medium ${readinessTone(readinessLevel)}`}>
        {readinessLevel}
      </p>

      <div className="mt-6 border-t border-ink-600 pt-6">
        <p className="text-sm leading-relaxed text-paper-300">
          {recommendationSummary}
        </p>
      </div>
    </div>
  );
}
