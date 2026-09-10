"use client";

import { useState } from "react";
import type { QuestionBreakdownRow } from "@/lib/types";

interface QuestionBreakdownAccordionProps {
  rows: QuestionBreakdownRow[];
}

function scoreTone(score: number): string {
  if (score >= 7) return "text-sage";
  if (score >= 4) return "text-amber";
  return "text-clay";
}

export default function QuestionBreakdownAccordion({
  rows,
}: QuestionBreakdownAccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="rounded-sm border border-ink-600 bg-ink-800">
      <h3 className="border-b border-ink-600 px-6 py-5 font-serif text-lg text-paper-100 sm:px-8">
        Question by question
      </h3>
      <div className="divide-y divide-ink-600">
        {rows.map((row, i) => {
          const isOpen = openIndex === i;
          return (
            <div key={i}>
              <button
                onClick={() => setOpenIndex(isOpen ? null : i)}
                className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left sm:px-8"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm text-paper-100">{row.question}</p>
                  <p className="mt-1 font-mono text-xs text-paper-300">
                    {row.category} · {row.difficulty}
                  </p>
                </div>
                <span
                  className={`shrink-0 font-mono text-sm ${scoreTone(row.score)}`}
                >
                  {row.score}/10
                </span>
              </button>
              {isOpen && (
                <div className="animate-cross-fade space-y-4 px-6 pb-6 sm:px-8">
                  <div>
                    <p className="mb-1.5 text-xs font-medium text-paper-300/70">
                      Your answer
                    </p>
                    <p className="text-sm leading-relaxed text-paper-100">
                      {row.answer || "No answer recorded."}
                    </p>
                  </div>
                  <div>
                    <p className="mb-1.5 text-xs font-medium text-paper-300/70">
                      Feedback
                    </p>
                    <p className="text-sm leading-relaxed text-paper-300">
                      {row.feedback}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
