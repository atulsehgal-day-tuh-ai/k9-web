# src/llm/mock_client.py
from __future__ import annotations

from typing import Protocol

from src.llm.payload import LLMPayload


class BaseLLMClient(Protocol):
    def generate(self, payload: LLMPayload) -> str:
        ...


class MockLLMClient:
    """
    MockLLMClient — K9 v1.0

    Cliente LLM determinista para testing.

    Permite simular:
    - interpretación válida (simple)
    - interpretación válida (composite)
    - interpretación inválida (fail-closed)
    - explicación parcial (explanation_i)
    - síntesis final (synthesis)
    - arrastre mínimo de contexto conversacional

    NO razona.
    NO decide flujo.
    NO mantiene estado interno.
    """

    # =====================================================
    # Entry
    # =====================================================
    def generate(self, payload: LLMPayload) -> str:
        phase = payload.active_phase

        if phase == "interpretation":
            return self._mock_interpretation(payload)

        if phase == "explanation_i":
            return self._mock_partial_explanation(payload)

        if phase == "synthesis":
            return self._mock_synthesis(payload)

        raise ValueError(f"Unknown LLM phase: {phase}")

    # =====================================================
    # Interpretation
    # =====================================================
    def _mock_interpretation(self, payload: LLMPayload) -> str:
        """
        Reglas deterministas:

        1) Pregunta ambigua → texto NO JSON → fail-closed
        2) Pregunta compuesta → COMPOSITE_K9_COMMAND
        3) Follow-up temporal → K9_COMMAND con operation=trend
        4) Pregunta clara simple → K9_COMMAND (status)
        """
        q = payload.user.original_question.lower()

        # -------------------------------------------------
        # FAIL-CLOSED explícito
        # -------------------------------------------------
        if "cosas" in q or ("seguridad" in q and "riesgos" not in q):
            return "No entiendo bien la pregunta."

        # -------------------------------------------------
        # FOLLOW-UP temporal (contexto conversacional)
        # -------------------------------------------------
        if any(
            kw in q
            for kw in [
                "desde entonces",
                "evolucion",
                "evolucionado",
                "último mes",
                "tendencia",
                "han evolucionado",
            ]
        ):
            return """
{
  "type": "K9_COMMAND",
  "intent": "ANALYTICAL_QUERY",
  "payload": {
    "intent": "ANALYTICAL_QUERY",
    "entity": "risk",
    "operation": "trend",
    "output": "narrative"
  }
}
""".strip()

        # -------------------------------------------------
        # COMPOSITE — pregunta con múltiples acciones
        # -------------------------------------------------
        if " y " in q:
            return """
{
  "type": "COMPOSITE_K9_COMMAND",
  "plan": [
    {
      "type": "K9_COMMAND",
      "intent": "ANALYTICAL_QUERY",
      "payload": {
        "intent": "ANALYTICAL_QUERY",
        "entity": "risk",
        "operation": "status",
        "output": "narrative"
      }
    },
    {
      "type": "K9_COMMAND",
      "intent": "ANALYTICAL_QUERY",
      "payload": {
        "intent": "ANALYTICAL_QUERY",
        "entity": "risk",
        "operation": "trend",
        "output": "narrative"
      }
    }
  ]
}
""".strip()

        # -------------------------------------------------
        # SIMPLE — caso canónico válido
        # -------------------------------------------------
        return """
{
  "type": "K9_COMMAND",
  "intent": "ANALYTICAL_QUERY",
  "payload": {
    "intent": "ANALYTICAL_QUERY",
    "entity": "risk",
    "operation": "status",
    "output": "narrative"
  }
}
""".strip()

    # =====================================================
    # explanation_i
    # =====================================================
    def _mock_partial_explanation(self, payload: LLMPayload) -> str:
        k9_cmd = payload.k9.k9_command or {}

        return (
            "[MOCK_PARTIAL_EXPLANATION]\n"
            f"Intent: {k9_cmd.get('intent')}\n"
            f"Entity: {k9_cmd.get('entity')}\n"
            f"Operation: {k9_cmd.get('operation')}\n"
        )

    # =====================================================
    # synthesis
    # =====================================================
    def _mock_synthesis(self, payload: LLMPayload) -> str:
        partials = payload.k9.partial_results or []

        lines = [
            "[MOCK_SYNTHESIS]",
            f"Total partial responses: {len(partials)}",
        ]

        for i, p in enumerate(partials, start=1):
            lines.append(f"- Partial {i}: {p.get('intent')}")

        return "\n".join(lines)
