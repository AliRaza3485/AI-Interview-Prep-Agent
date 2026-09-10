import type { Evaluation } from "@/lib/types";

interface EvaluationFeedbackProps {
  evaluation: Evaluation;
  isLastQuestion: boolean;
  onContinue: () => void;
}

function scoreTone(score: number): string {
  if (score >= 7) return "text-sage border-sage/40";
  if (score >= 4) return "text-amber border-amber/40";
  return "text-clay border-clay/40";
}

export default function EvaluationFeedback({
  evaluation,
  isLastQuestion,
  onContinue,
}: EvaluationFeedbackProps) {
  return (
    <div className="animate-cross-fade mt-8 rounded-sm border border-ink-600 bg-ink-800 p-6 sm:p-8">
      <div className="flex items-start gap-4">
        <div
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border font-mono text-lg ${scoreTone(
            evaluation.score
          )}`}
        >
          {evaluation.score}
        </div>
        <p className="pt-1.5 text-paper-100">{evaluation.feedback}</p>
      </div>

      {(evaluation.strengths_shown.length > 0 ||
        evaluation.improvement_areas.length > 0) && (
        <div className="mt-6 grid gap-6 border-t border-ink-600 pt-6 sm:grid-cols-2">
          {evaluation.strengths_shown.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-sage">What landed</h4>
              <ul className="space-y-1.5">
                {evaluation.strengths_shown.map((s, i) => (
                  <li key={i} className="text-sm text-paper-300">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {evaluation.improvement_areas.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-clay">
                Worth sharpening
              </h4>
              <ul className="space-y-1.5">
                {evaluation.improvement_areas.map((s, i) => (
                  <li key={i} className="text-sm text-paper-300">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button
          onClick={onContinue}
          className="rounded-sm border border-ink-600 px-6 py-2.5 text-sm font-medium text-paper-100 transition-colors hover:border-amber hover:text-amber"
        >
          {isLastQuestion ? "See your report" : "Next question"}
        </button>
      </div>
    </div>
  );
}
