"use client";

import { useMemo, useState } from "react";

type Tab = "summary" | "trace" | "recommendations" | "raw";

export function InspectorPanel({
  labels,
  result,
}: {
  labels: { summary: string; trace: string; recommendations: string; raw: string };
  result: any;
}) {
  const [tab, setTab] = useState<Tab>("summary");

  const pretty = useMemo(() => {
    try {
      const v =
        tab === "trace"
          ? result?.trace
          : tab === "recommendations"
            ? result?.recommendations
            : tab === "summary"
              ? {
                  risk_summary: result?.analysis?.risk_summary,
                  metrics_rankings: result?.analysis?.metrics?.rankings,
                }
              : result;
      return JSON.stringify(v ?? null, null, 2);
    } catch {
      return String(result);
    }
  }, [result, tab]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "summary", label: labels.summary },
    { id: "trace", label: labels.trace },
    { id: "recommendations", label: labels.recommendations },
    { id: "raw", label: labels.raw },
  ];

  return (
    <div className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex flex-wrap items-center gap-2 border-b border-zinc-200 px-3 py-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={[
              "rounded-lg px-3 py-1.5 text-xs font-semibold",
              tab === t.id ? "bg-zinc-900 text-white" : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200",
            ].join(" ")}
          >
            {t.label}
          </button>
        ))}
      </div>
      <pre className="max-h-[52vh] overflow-auto bg-zinc-50 p-4 text-xs leading-5 text-zinc-900">{pretty}</pre>
    </div>
  );
}

