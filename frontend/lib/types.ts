// These mirror the Pydantic response models in backend/api/*.py exactly.
// Keep this file in sync with the backend if the schemas change.

export type QuestionCategory = "technical" | "behavioral" | "project_deep_dive";
export type QuestionDifficulty = "easy" | "medium" | "hard";

export interface Question {
  question: string;
  category: QuestionCategory;
  difficulty: QuestionDifficulty;
  targets: string;
}

export interface GapAnalysis {
  strengths: string[];
  gaps: string[];
  partial_matches: string[];
  focus_areas: string[];
}

export interface Evaluation {
  score: number; // 0-10
  feedback: string;
  strengths_shown: string[];
  improvement_areas: string[];
}

// Response of POST /interview/begin
export interface BeginInterviewResponse {
  session_id: string;
  is_complete: boolean;
  question: Question | null;
  question_number: number | null;
  total_questions: number;
  gap_analysis: GapAnalysis;
  resume_data: Record<string, unknown>;
  jd_data: Record<string, unknown>;
}

// Response of POST /interview/next-question
export interface NextQuestionResponse {
  is_complete: boolean;
  question: Question | null;
  question_number: number | null;
  total_questions: number;
}

// Response of POST /interview/submit-answer
export interface SubmitAnswerResponse {
  evaluation: Evaluation;
  is_complete: boolean;
  next_question: Question | null;
  question_number: number | null;
  total_questions: number;
}

export interface CategoryBreakdownEntry {
  average_score: number;
  questions_count: number;
}

export interface QuestionBreakdownRow {
  question: string;
  category: string;
  difficulty: string;
  answer: string;
  score: number;
  feedback: string;
}

// Response of POST /interview/report
export interface ReportResponse {
  overall_score: number;
  readiness_level: string;
  category_breakdown: Record<string, CategoryBreakdownEntry>;
  gaps_addressed: string[];
  gaps_still_open: string[];
  key_strengths: string[];
  key_weaknesses: string[];
  recommendation_summary: string;
  question_breakdown: QuestionBreakdownRow[];
}

export interface ApiErrorBody {
  detail: string;
}
