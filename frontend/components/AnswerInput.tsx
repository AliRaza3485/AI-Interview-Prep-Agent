interface AnswerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export default function AnswerInput({
  value,
  onChange,
  onSubmit,
  isSubmitting,
}: AnswerInputProps) {
  return (
    <div className="mt-8">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Answer as you would out loud — structure matters more than length."
        rows={8}
        disabled={isSubmitting}
        className="w-full resize-y rounded-sm px-4 py-3 text-sm leading-relaxed text-paper-100 placeholder:text-paper-300/60 disabled:opacity-60"
      />
      <div className="mt-4 flex justify-end">
        <button
          onClick={onSubmit}
          disabled={isSubmitting || value.trim().length === 0}
          className="rounded-sm bg-amber px-6 py-2.5 text-sm font-medium text-ink-900 transition-colors hover:bg-amber-dim disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isSubmitting ? "Reflecting on your answer…" : "Submit answer"}
        </button>
      </div>
    </div>
  );
}
