"use client";

import type { Lang } from "@/lib/i18n";

export function LanguageToggle({
  value,
  onChange,
  labels,
}: {
  value: Lang;
  onChange: (lang: Lang) => void;
  labels: { language: string; english: string; spanish: string };
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-medium text-zinc-500">{labels.language}</span>
      <div className="inline-flex overflow-hidden rounded-lg border border-zinc-200 bg-white">
        <button
          type="button"
          onClick={() => onChange("en")}
          className={[
            "px-2.5 py-1 text-xs font-semibold",
            value === "en" ? "bg-zinc-900 text-white" : "bg-white text-zinc-700 hover:bg-zinc-50",
          ].join(" ")}
        >
          {labels.english}
        </button>
        <button
          type="button"
          onClick={() => onChange("es")}
          className={[
            "px-2.5 py-1 text-xs font-semibold",
            value === "es" ? "bg-zinc-900 text-white" : "bg-white text-zinc-700 hover:bg-zinc-50",
          ].join(" ")}
        >
          {labels.spanish}
        </button>
      </div>
    </div>
  );
}

