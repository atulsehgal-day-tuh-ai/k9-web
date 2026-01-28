export type Lang = "en" | "es";

export const STRINGS: Record<Lang, Record<string, string>> = {
  en: {
    appTitle: "K9 Mining Safety",
    appSubtitle: "Dashboard + Chat (Demo)",
    chatTitle: "Chat",
    chatHint:
      "Ask about dominant risk, trends, proactive misalignment, observations, or the ontology.",
    tryLabel: "Try:",
    inputPlaceholder: "Type your question…",
    send: "Send",
    demoControls: "Demo controls",
    criticalMondayOn: "Critical Monday: ON",
    criticalMondayOff: "Critical Monday: OFF",
    dominantRisk: "Dominant risk",
    relevantRisk: "Relevant risk",
    highestAvgCrit: "Highest avg criticality",
    degradingTrajectory: "Degrading trajectory",
    latestResultRaw: "Latest result (raw)",
    metrics: "analysis.metrics",
    reasoning: "reasoning",
    trace: "trace",
    recommendations: "recommendations",
    inspectorSummary: "Summary",
    inspectorTrace: "Trace",
    inspectorRecommendations: "Recommendations",
    inspectorRaw: "Raw",
    trajectoriesTitle: "Risk trajectories",
    requestFailed: "Request failed",
    assistantError: "I couldn't process the request.",
    assistantClarify: "I need a bit more precision to continue.",
    unknownResponse: "Unrecognized response.",
    language: "Language",
    english: "English",
    spanish: "Spanish",
  },
  es: {
    appTitle: "K9 Mining Safety",
    appSubtitle: "Dashboard + Chat (Demo)",
    chatTitle: "Chat",
    chatHint:
      "Pregunta por riesgo dominante, tendencias, desalineación proactiva, observaciones u ontología.",
    tryLabel: "Prueba:",
    inputPlaceholder: "Escribe tu pregunta…",
    send: "Enviar",
    demoControls: "Controles demo",
    criticalMondayOn: "Lunes Crítico: ON",
    criticalMondayOff: "Lunes Crítico: OFF",
    dominantRisk: "Riesgo dominante",
    relevantRisk: "Riesgo relevante",
    highestAvgCrit: "Mayor criticidad promedio",
    degradingTrajectory: "Trayectoria degradante",
    latestResultRaw: "Último resultado (raw)",
    metrics: "analysis.metrics",
    reasoning: "razonamiento",
    trace: "traza",
    recommendations: "recomendaciones",
    inspectorSummary: "Resumen",
    inspectorTrace: "Traza",
    inspectorRecommendations: "Recomendaciones",
    inspectorRaw: "Raw",
    trajectoriesTitle: "Trayectorias de riesgo",
    requestFailed: "La solicitud falló",
    assistantError: "No pude procesar la solicitud.",
    assistantClarify: "Necesito un poco más de precisión para continuar.",
    unknownResponse: "Respuesta no reconocida.",
    language: "Idioma",
    english: "Inglés",
    spanish: "Español",
  },
};

export function normalizeLang(input: unknown): Lang {
  const s = String(input || "").toLowerCase();
  if (s.startsWith("es")) return "es";
  return "en";
}

