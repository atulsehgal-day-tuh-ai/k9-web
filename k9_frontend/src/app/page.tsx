/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useMemo, useState } from "react";
import { JsonBlock } from "@/components/JsonBlock";
import { KpiCard } from "@/components/KpiCard";
import { LanguageToggle } from "@/components/LanguageToggle";
import { InspectorPanel } from "@/components/InspectorPanel";
import { TrajectoryChart } from "@/components/TrajectoryChart";
import { normalizeLang, STRINGS, type Lang } from "@/lib/i18n";

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string; raw?: any }>
  >([]);
  const [latestResult, setLatestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [criticalMondayEnabled, setCriticalMondayEnabled] = useState(false);
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("k9_lang");
      if (stored) {
        setLang(normalizeLang(stored));
        return;
      }
      setLang(normalizeLang(window.navigator.language));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem("k9_lang", lang);
    } catch {
      // ignore
    }
  }, [lang]);

  const t = useMemo(() => STRINGS[lang], [lang]);

  const riskSummary = useMemo(() => {
    const analysis = latestResult?.analysis || {};
    return analysis?.risk_summary || null;
  }, [latestResult]);

  const metrics = useMemo(() => {
    const analysis = latestResult?.analysis || {};
    return analysis?.metrics || null;
  }, [latestResult]);

  const trajectories = useMemo(() => {
    const ts = metrics?.time_series?.risk_trajectories || null;
    if (!ts || typeof ts !== "object") return null;
    return ts as Record<string, { weekly_values?: number[] }>;
  }, [metrics]);

  const demoQuestions = useMemo(() => {
    if (lang === "es") {
      return [
        "¿Cuál es el riesgo dominante hoy?",
        "Explica por qué el riesgo dominante es el más crítico. ¿Qué factores causales y de exposición están asociados?",
        "Muéstrame la evolución del riesgo R02 en el último mes.",
        "Compara R01 vs R02: ¿cuál está empeorando más en las últimas 4 semanas?",
        "¿Cuántas observaciones tuvimos en la última semana y en qué áreas ocurrieron?",
        "¿Qué auditorías reactivas ocurrieron después de eventos en los últimos 14 días?",
        "¿Hay desalineación con el modelo proactivo esta semana? ¿Qué umbrales se cruzaron?",
        "Antes y después de “Lunes Crítico”: ¿cómo cambió el ranking de riesgos?",
        "Para el riesgo dominante, ¿cuáles son los controles críticos y barreras de recuperación recomendadas?",
        "¿Qué cambió en los últimos 7 días que explica el aumento del riesgo relevante?",
      ];
    }
    return [
      "What is the dominant risk today?",
      "Explain why the dominant risk is the most critical. What causal and exposure factors are associated?",
      "Show me the evolution of risk R02 over the last month.",
      "Compare R01 vs R02: which one is worsening more over the last 4 weeks?",
      "How many observations did we have in the last week and in which areas did they occur?",
      "Which reactive audits occurred after events in the last 14 days?",
      "Is there misalignment with the proactive model this week? Which thresholds were crossed?",
      "Before and after “Critical Monday”: how did the risk ranking change?",
      "For the dominant risk, what are the recommended critical controls and recovery barriers?",
      "What changed in the last 7 days that explains the increase of the relevant risk?",
    ];
  }, [lang]);

  async function toggleCriticalMonday(enabled: boolean) {
    setError(null);
    setCriticalMondayEnabled(enabled);
    try {
      const res = await fetch("/api/critical-monday", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Failed to toggle scenario");
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setLoading(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: "dev", message: text, language: lang }),
      });

      const data = await res.json();

      if (!res.ok || data?.type === "error") {
        setError(data?.message || t.requestFailed);
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: t.assistantError,
            raw: data,
          },
        ]);
        return;
      }

      if (data?.type === "clarify") {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content:
              data?.clarification?.reason || t.assistantClarify,
            raw: data,
          },
        ]);
        setLatestResult(data);
        return;
      }

      if (data?.type === "result") {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: data?.answer || "(sin respuesta)",
            raw: data,
          },
        ]);
        setLatestResult(data);
        return;
      }

      setMessages((m) => [
        ...m,
        { role: "assistant", content: t.unknownResponse, raw: data },
      ]);
      setLatestResult(data);
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div>
            <div className="text-sm font-semibold text-zinc-900">
              {t.appTitle}
            </div>
            <div className="text-xs text-zinc-500">{t.appSubtitle}</div>
          </div>
          <div className="flex items-center gap-4">
            <LanguageToggle
              value={lang}
              onChange={setLang}
              labels={{ language: t.language, english: t.english, spanish: t.spanish }}
            />
            <div className="hidden text-xs text-zinc-500 sm:block">
              Backend:{" "}
              <span className="font-mono">
                {process.env.K9_API_BASE_URL || "proxied via /api/chat"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-4 px-4 py-6 lg:grid-cols-12">
        <section className="lg:col-span-5">
          <div className="rounded-xl border border-zinc-200 bg-white shadow-sm">
            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-900">{t.chatTitle}</div>
              <div className="text-xs text-zinc-500">{t.chatHint}</div>
            </div>

            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-xs font-semibold text-zinc-900">{t.demoControls}</div>
                <button
                  type="button"
                  onClick={() => void toggleCriticalMonday(!criticalMondayEnabled)}
                  className={[
                    "rounded-lg px-3 py-1.5 text-xs font-semibold",
                    criticalMondayEnabled
                      ? "bg-amber-100 text-amber-900 border border-amber-200"
                      : "bg-zinc-100 text-zinc-900 border border-zinc-200",
                  ].join(" ")}
                >
                  {criticalMondayEnabled ? t.criticalMondayOn : t.criticalMondayOff}
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {demoQuestions.slice(0, 4).map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setInput(q)}
                    className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
                    title="Click to copy into the input"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-[60vh] overflow-auto px-4 py-4">
              {messages.length === 0 ? (
                <div className="text-sm text-zinc-500">
                  {t.tryLabel}{" "}
                  <span className="font-medium">
                    {demoQuestions[0]}
                  </span>
                </div>
              ) : null}

              <div className="space-y-3">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={m.role === "user" ? "text-right" : "text-left"}
                  >
                    <div
                      className={[
                        "inline-block max-w-[90%] rounded-2xl px-3 py-2 text-sm",
                        m.role === "user"
                          ? "bg-zinc-900 text-white"
                          : "bg-zinc-100 text-zinc-900",
                      ].join(" ")}
                    >
                      {m.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-zinc-200 p-3">
              {error ? (
                <div className="mb-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                  {error}
                </div>
              ) : null}
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void send();
                  }}
                  placeholder={t.inputPlaceholder}
                  className="flex-1 rounded-xl border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-900"
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void send()}
                  className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {loading ? "…" : t.send}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4 lg:col-span-7">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <KpiCard
              label={t.dominantRisk}
              value={riskSummary?.dominant_risk ? String(riskSummary.dominant_risk) : "—"}
              sublabel={t.highestAvgCrit}
            />
            <KpiCard
              label={t.relevantRisk}
              value={riskSummary?.relevant_risk ? String(riskSummary.relevant_risk) : "—"}
              sublabel={t.degradingTrajectory}
            />
          </div>

          <TrajectoryChart
            title={t.trajectoriesTitle}
            series={[
              ...(riskSummary?.dominant_risk && trajectories?.[riskSummary.dominant_risk]?.weekly_values
                ? [
                    {
                      id: String(riskSummary.dominant_risk),
                      values: trajectories[riskSummary.dominant_risk].weekly_values || [],
                      color: "#0F172A",
                    },
                  ]
                : []),
              ...(riskSummary?.relevant_risk &&
              riskSummary.relevant_risk !== riskSummary.dominant_risk &&
              trajectories?.[riskSummary.relevant_risk]?.weekly_values
                ? [
                    {
                      id: String(riskSummary.relevant_risk),
                      values: trajectories[riskSummary.relevant_risk].weekly_values || [],
                      color: "#F59E0B",
                    },
                  ]
                : []),
            ]}
          />

          <InspectorPanel
            labels={{
              summary: t.inspectorSummary,
              trace: t.inspectorTrace,
              recommendations: t.inspectorRecommendations,
              raw: t.inspectorRaw,
            }}
            result={latestResult}
          />

          {/* Keep these blocks available for quick debugging in dev */}
          <div className="hidden">
            <JsonBlock title={t.latestResultRaw} value={latestResult} />
            <JsonBlock title={t.metrics} value={metrics} />
            <JsonBlock title={t.reasoning} value={latestResult?.reasoning || []} />
            <JsonBlock title={t.trace} value={latestResult?.trace || null} />
            <JsonBlock title={t.recommendations} value={latestResult?.recommendations || null} />
          </div>
        </section>
      </main>
    </div>
  );
}
