interface GapsAndStrengthsProps {
  gapsAddressed: string[];
  gapsStillOpen: string[];
  keyStrengths: string[];
  keyWeaknesses: string[];
}

function Column({
  title,
  items,
  tone,
  emptyText,
}: {
  title: string;
  items: string[];
  tone: "sage" | "clay";
  emptyText: string;
}) {
  const dotColor = tone === "sage" ? "bg-sage" : "bg-clay";
  const titleColor = tone === "sage" ? "text-sage" : "text-clay";

  return (
    <div>
      <h4 className={`mb-3 text-sm font-medium ${titleColor}`}>{title}</h4>
      {items.length === 0 ? (
        <p className="text-sm text-paper-300/70">{emptyText}</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className="flex gap-3 text-sm text-paper-100">
              <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dotColor}`} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function GapsAndStrengths({
  gapsAddressed,
  gapsStillOpen,
  keyStrengths,
  keyWeaknesses,
}: GapsAndStrengthsProps) {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <div className="rounded-sm border border-ink-600 bg-ink-800 p-6 sm:p-8">
        <h3 className="mb-6 font-serif text-lg text-paper-100">
          Job-requirement gaps
        </h3>
        <div className="space-y-6">
          <Column
            title="Addressed well"
            items={gapsAddressed}
            tone="sage"
            emptyText="None fully closed yet."
          />
          <Column
            title="Still open"
            items={gapsStillOpen}
            tone="clay"
            emptyText="Nothing left open — good sign."
          />
        </div>
      </div>

      <div className="rounded-sm border border-ink-600 bg-ink-800 p-6 sm:p-8">
        <h3 className="mb-6 font-serif text-lg text-paper-100">
          Across the interview
        </h3>
        <div className="space-y-6">
          <Column
            title="Key strengths"
            items={keyStrengths}
            tone="sage"
            emptyText="Not enough signal yet."
          />
          <Column
            title="Key weaknesses"
            items={keyWeaknesses}
            tone="clay"
            emptyText="Nothing notable."
          />
        </div>
      </div>
    </div>
  );
}
