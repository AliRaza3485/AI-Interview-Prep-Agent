"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { ReportResponse } from "@/lib/types";
import { getReport } from "@/lib/api";
import ReportSummary from "@/components/ReportSummary";
import CategoryBreakdownChart from "@/components/CategoryBreakdownChart";
import GapsAndStrengths from "@/components/GapsAndStrengths";
import QuestionBreakdownAccordion from "@/components/QuestionBreakdownAccordion";

export default function ReportPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getReport(sessionId)
      .then(setReport)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Couldn't load the report.")
      );
  }, [sessionId]);

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6">
        <p className="rounded-sm border border-clay/40 bg-clay/10 px-4 py-3 text-sm text-clay">
          {error}
        </p>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6">
        <p className="text-paper-300">Putting your report together…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-16 sm:py-20">
      <h1 className="font-serif text-3xl text-paper-100 sm:text-4xl">
        How it went
      </h1>

      <div className="mt-10 grid gap-8 lg:grid-cols-[18rem_1fr]">
        <div className="lg:sticky lg:top-16 lg:self-start">
          <ReportSummary
            overallScore={report.overall_score}
            readinessLevel={report.readiness_level}
            recommendationSummary={report.recommendation_summary}
          />
        </div>

        <div className="space-y-6">
          <CategoryBreakdownChart breakdown={report.category_breakdown} />
          <GapsAndStrengths
            gapsAddressed={report.gaps_addressed}
            gapsStillOpen={report.gaps_still_open}
            keyStrengths={report.key_strengths}
            keyWeaknesses={report.key_weaknesses}
          />
          <QuestionBreakdownAccordion rows={report.question_breakdown} />
        </div>
      </div>
    </main>
  );
}
