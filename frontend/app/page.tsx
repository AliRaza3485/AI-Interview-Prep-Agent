"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ResumeUpload from "@/components/ResumeUpload";
import JDInput from "@/components/JDInput";
import { beginInterview } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = resumeFile !== null && jdText.trim().length > 0 && !isSubmitting;

  async function handleStart() {
    if (!resumeFile || jdText.trim().length === 0) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await beginInterview(resumeFile, jdText);
      // Stash the fresh session's opening state so the interview room can
      // render instantly without an extra round trip, and so it knows to
      // show the gap-analysis preview once before the first question.
      sessionStorage.setItem(
        `interview:${result.session_id}`,
        JSON.stringify(result)
      );
      router.push(`/interview/${result.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-prose flex-col justify-center px-6 py-20">
      <div className="mb-12">
        <h1 className="font-serif text-4xl leading-tight text-paper-100 sm:text-5xl">
          Before the real interview,
          <br />
          have this one.
        </h1>
        <p className="mt-4 text-paper-300">
          Give it your resume and the job you&apos;re after. It finds exactly
          where the two don&apos;t line up, then interviews you on precisely
          that — with reasoning behind every score, not just a number.
        </p>
      </div>

      <div className="space-y-8">
        <ResumeUpload file={resumeFile} onChange={setResumeFile} />
        <JDInput value={jdText} onChange={setJdText} />
      </div>

      {error && (
        <p className="mt-6 rounded-sm border border-clay/40 bg-clay/10 px-4 py-3 text-sm text-clay">
          {error}
        </p>
      )}

      <div className="mt-8 flex justify-end">
        <button
          onClick={handleStart}
          disabled={!canSubmit}
          className="rounded-sm bg-amber px-6 py-3 text-sm font-medium text-ink-900 transition-colors hover:bg-amber-dim disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isSubmitting ? "Reading your resume…" : "Start interview prep"}
        </button>
      </div>
    </main>
  );
}
