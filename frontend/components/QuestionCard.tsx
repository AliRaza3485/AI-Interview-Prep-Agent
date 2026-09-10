import type { Question } from "@/lib/types";

interface QuestionCardProps {
  question: Question;
}

const CATEGORY_LABEL: Record<Question["category"], string> = {
  technical: "Technical",
  behavioral: "Behavioral",
  project_deep_dive: "Project deep dive",
};

const DIFFICULTY_LABEL: Record<Question["difficulty"], string> = {
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
};

export default function QuestionCard({ question }: QuestionCardProps) {
  return (
    <div className="animate-cross-fade">
      <div className="mb-4 flex flex-wrap items-center gap-2 font-mono text-xs text-paper-300">
        <span className="rounded-sm border border-ink-600 px-2 py-1">
          {CATEGORY_LABEL[question.category]}
        </span>
        <span className="rounded-sm border border-ink-600 px-2 py-1">
          {DIFFICULTY_LABEL[question.difficulty]}
        </span>
      </div>
      <p className="font-serif text-2xl leading-snug text-paper-100 sm:text-3xl">
        {question.question}
      </p>
    </div>
  );
}
