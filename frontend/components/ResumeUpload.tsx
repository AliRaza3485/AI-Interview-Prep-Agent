"use client";

import { useRef, useState } from "react";

interface ResumeUploadProps {
  file: File | null;
  onChange: (file: File | null) => void;
}

const ACCEPTED = [".pdf", ".docx"];

function isAccepted(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED.some((ext) => name.endsWith(ext));
}

export default function ResumeUpload({ file, onChange }: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(fileList: FileList | null) {
    const picked = fileList?.[0];
    if (!picked) return;
    if (!isAccepted(picked)) {
      setError("Only PDF or DOCX files are supported.");
      return;
    }
    setError(null);
    onChange(picked);
  }

  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-paper-300">
        Resume
      </label>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-sm border px-6 py-10 text-center transition-colors ${
          isDragging
            ? "border-amber bg-ink-700"
            : "border-dashed border-ink-600 bg-ink-800 hover:border-ink-600/80"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {file ? (
          <div>
            <p className="font-medium text-paper-100">{file.name}</p>
            <p className="mt-1 text-sm text-paper-300">
              {(file.size / 1024).toFixed(0)} KB · click to replace
            </p>
          </div>
        ) : (
          <div>
            <p className="text-paper-100">
              Drop your resume here, or click to browse
            </p>
            <p className="mt-1 text-sm text-paper-300">PDF or DOCX</p>
          </div>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-clay">{error}</p>}
    </div>
  );
}
