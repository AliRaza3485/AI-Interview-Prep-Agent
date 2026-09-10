interface ProgressBarProps {
  current: number; // 1-indexed question number
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const pct = total > 0 ? Math.min(100, ((current - 1) / total) * 100) : 0;

  return (
    <div>
      <div className="h-[3px] w-full overflow-hidden rounded-full bg-ink-700">
        <div
          className="h-full rounded-full bg-amber transition-[width] duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-3 text-sm text-paper-300">
        Question {current} of {total}
      </p>
    </div>
  );
}
