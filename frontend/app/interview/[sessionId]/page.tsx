"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type {
  BeginInterviewResponse,
  Evaluation,
  GapAnalysis,
  Question,
} from "@/lib/types";
import { getNextQuestion, submitAnswer } from "@/lib/api";
import GapAnalysisPreview from "@/components/GapAnalysisPreview";
import ProgressBar from "@/components/ProgressBar";
import QuestionCard from "@/components/QuestionCard";
import AnswerInput from "@/components/AnswerInput";
import EvaluationFeedback from "@/components/EvaluationFeedback";

type Phase = "loading" | "preview" | "question" | "feedback";

export default function InterviewRoomPage() {
  const router = useRouter();
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;

  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);

  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);

  const [activeQuestion, setActiveQuestion] = useState<Question | null>(null);
  const [activeQuestionNumber, setActiveQuestionNumber] = useState<number | null>(
    null
  );
  const [totalQuestions, setTotalQuestions] = useState(0);

  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [lastEvaluation, setLastEvaluation] = useState<Evaluation | null>(null);
  const [pendingComplete, setPendingComplete] = useState(false);
  const [pendingNextQuestion, setPendingNextQuestion] = useState<Question | null>(
    null
  );
  const [pendingNextNumber, setPendingNextNumber] = useState<number | null>(null);

  // On mount: use the cached "fresh start" payload if this is the first
  // visit right after /interview/begin, otherwise resync from the backend
  // (covers refreshes, back-navigation, and shared links).
  useEffect(() => {
    if (!sessionId) return;

    const cacheKey = `interview:${sessionId}`;
    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
      sessionStorage.removeItem(cacheKey);
      const data: BeginInterviewResponse = JSON.parse(cached);

      if (data.is_complete) {
        router.replace(`/interview/${sessionId}/report`);
        return;
      }

      setGapAnalysis(data.gap_analysis);
      setActiveQuestion(data.question);
      setActiveQuestionNumber(data.question_number);
      setTotalQuestions(data.total_questions);
      setPhase("preview");
      return;
    }

    getNextQuestion(sessionId)
      .then((data) => {
        if (data.is_complete) {
          router.replace(`/interview/${sessionId}/report`);
          return;
        }
        setActiveQuestion(data.question);
        setActiveQuestionNumber(data.question_number);
        setTotalQuestions(data.total_questions);
        setPhase("question");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Couldn't load this session.");
      });
  }, [sessionId, router]);

  async function handleSubmitAnswer() {
    if (!sessionId || answer.trim().length === 0) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await submitAnswer(sessionId, answer);
      setLastEvaluation(result.evaluation);
      setPendingComplete(result.is_complete);
      setPendingNextQuestion(result.next_question);
      setPendingNextNumber(result.question_number);
      setPhase("feedback");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't submit that answer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleContinue() {
    if (pendingComplete) {
      router.push(`/interview/${sessionId}/report`);
      return;
    }
    setActiveQuestion(pendingNextQuestion);
    setActiveQuestionNumber(pendingNextNumber);
    setAnswer("");
    setLastEvaluation(null);
    setPhase("question");
  }

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6">
        <p className="rounded-sm border border-clay/40 bg-clay/10 px-4 py-3 text-sm text-clay">
          {error}
        </p>
      </main>
    );
  }

  if (phase === "loading") {
    return (
      <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6">
        <p className="text-paper-300">Setting up your session…</p>
      </main>
    );
  }

  if (phase === "preview" && gapAnalysis) {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-6 py-20">
        <GapAnalysisPreview gapAnalysis={gapAnalysis} />
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => setPhase("question")}
            className="rounded-sm bg-amber px-6 py-2.5 text-sm font-medium text-ink-900 transition-colors hover:bg-amber-dim"
          >
            Begin the interview
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6 py-20">
      {activeQuestionNumber !== null && (
        <div className="mb-10">
          <ProgressBar current={activeQuestionNumber} total={totalQuestions} />
        </div>
      )}

      {activeQuestion && <QuestionCard question={activeQuestion} />}

      {phase === "question" && (
        <AnswerInput
          value={answer}
          onChange={setAnswer}
          onSubmit={handleSubmitAnswer}
          isSubmitting={isSubmitting}
        />
      )}

      {phase === "feedback" && lastEvaluation && (
        <EvaluationFeedback
          evaluation={lastEvaluation}
          isLastQuestion={pendingComplete}
          onContinue={handleContinue}
        />
      )}
    </main>
  );
}
