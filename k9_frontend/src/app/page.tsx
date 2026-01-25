/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useMemo, useState } from "react";
import { JsonBlock } from "@/components/JsonBlock";
import { KpiCard } from "@/components/KpiCard";

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string; raw?: any }>
  >([]);
  const [latestResult, setLatestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const riskSummary = useMemo(() => {
    const analysis = latestResult?.analysis || {};
    return analysis?.risk_summary || null;
  }, [latestResult]);

  const metrics = useMemo(() => {
    const analysis = latestResult?.analysis || {};
    return analysis?.metrics || null;
  }, [latestResult]);

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
        body: JSON.stringify({ sessionId: "dev", message: text }),
      });

      const data = await res.json();

      if (!res.ok || data?.type === "error") {
        setError(data?.message || "Request failed");
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: "No pude procesar la solicitud.",
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
              data?.clarification?.reason ||
              "Necesito un poco más de precisión para continuar.",
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
        { role: "assistant", content: "Respuesta no reconocida.", raw: data },
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
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <div className="text-sm font-semibold text-zinc-900">
              K9 Mining Safety
            </div>
            <div className="text-xs text-zinc-500">Dashboard + Chat (DEV)</div>
          </div>
          <div className="text-xs text-zinc-500">
            Backend:{" "}
            <span className="font-mono">
              {process.env.K9_API_BASE_URL || "proxied via /api/chat"}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-4 py-6 lg:grid-cols-5">
        <section className="lg:col-span-2">
          <div className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-900">Chat</div>
              <div className="text-xs text-zinc-500">
                Pregunta por riesgo dominante, tendencias, desalineación proactiva, observaciones u ontología.
              </div>
            </div>

            <div className="h-[60vh] overflow-auto px-4 py-4">
              {messages.length === 0 ? (
                <div className="text-sm text-zinc-500">
                  Try:{" "}
                  <span className="font-medium">
                    ¿Cuál es el riesgo dominante hoy?
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
                  placeholder="Escribe tu pregunta…"
                  className="flex-1 rounded-xl border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-900"
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void send()}
                  className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {loading ? "…" : "Send"}
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4 lg:col-span-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <KpiCard
              label="Dominant risk"
              value={riskSummary?.dominant_risk ? String(riskSummary.dominant_risk) : "—"}
              sublabel="Highest avg criticidad"
            />
            <KpiCard
              label="Relevant risk"
              value={riskSummary?.relevant_risk ? String(riskSummary.relevant_risk) : "—"}
              sublabel="Degrading trajectory"
            />
          </div>

          <JsonBlock title="Latest result (raw)" value={latestResult} />
          <JsonBlock title="analysis.metrics" value={metrics} />
          <JsonBlock title="reasoning" value={latestResult?.reasoning || []} />
        </section>
      </main>
    </div>
  );
}
