interface JDInputProps {
  value: string;
  onChange: (value: string) => void;
}

export default function JDInput({ value, onChange }: JDInputProps) {
  return (
    <div>
      <label
        htmlFor="jd-text"
        className="mb-2 block text-sm font-medium text-paper-300"
      >
        Job description
      </label>
      <textarea
        id="jd-text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste the full job posting here — the more detail, the sharper the gap analysis."
        rows={10}
        className="w-full resize-y rounded-sm px-4 py-3 text-sm leading-relaxed text-paper-100 placeholder:text-paper-300/60"
      />
    </div>
  );
}
