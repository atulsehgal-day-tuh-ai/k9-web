from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from src.state.state import K9State
from src.llm.payload import (
    LLMPayload,
    LLMSystemContract,
    LLMUserContext,
    LLMK9Context,
)
from src.llm.validators import validate_llm_output_schema
from src.llm.clarification_log import log_clarification_event


class LLMNode:
    """
    LLMNode — interfaz lingüística de K9.

    Responsabilidad:
    - Interpretation: NL -> K9_COMMAND / COMPOSITE_K9_COMMAND / CLARIFICATION_REQUEST
    - Synthesis:      narrative/analysis -> FINAL_ANSWER

    Reglas:
    - Nunca ejecuta lógica de negocio.
    - Fail-closed cuando el output no cumple contrato.
    """

    def __init__(self, *, llm_client: Any, knowledge_scaffold: Any):
        self.llm_client = llm_client
        self.knowledge_scaffold = knowledge_scaffold

    # ==================================================
    # Callable
    # ==================================================
    def __call__(self, state: K9State) -> K9State:
        phase = self._resolve_phase(state)

        # En synthesis, si alguien olvida setear session_context, lo creamos (infra, no cognición)
        if phase == "synthesis" and state.llm_session_context is None:
            from src.llm.session_context import LLMSessionContext

            state.llm_session_context = LLMSessionContext(
                session_id=f"auto-{uuid.uuid4().hex[:8]}",
                active_phase="synthesis",
            )

        payload = self._build_payload(state, phase)

        raw_response = self._call_llm(payload)

        parsed = self._safe_parse_json(raw_response)

        # -------------------------------------------------
        # INTERPRETATION
        # -------------------------------------------------
        if phase == "interpretation":
            return self._handle_interpretation(state, parsed, raw_response)

        # -------------------------------------------------
        # SYNTHESIS
        # -------------------------------------------------
        if phase == "synthesis":
            return self._handle_synthesis(state, parsed, raw_response)

        # -------------------------------------------------
        # Safety net (no debería pasar)
        # -------------------------------------------------
        state.answer = raw_response
        return state

    # ==================================================
    # LLM call adapter (robusto)
    # ==================================================
    def _call_llm(self, payload: LLMPayload) -> str:
        """
        Contrato: intentamos, en este orden:
        1) llm_client.generate(payload)           (tu contrato actual)
        2) llm_client.generate(payload.render())  (clientes que esperan string)
        3) llm_client.complete(payload.render())  (compatibilidad legacy)
        4) llm_client(payload.render())           (callable)
        """
        # 1) generate(payload)
        if hasattr(self.llm_client, "generate"):
            try:
                return self.llm_client.generate(payload)
            except TypeError:
                # 2) generate(prompt_string)
                return self.llm_client.generate(payload.render())

        prompt = payload.render()

        # 3) complete(prompt_string)
        if hasattr(self.llm_client, "complete"):
            return self.llm_client.complete(prompt)

        # 4) callable(prompt_string)
        if callable(self.llm_client):
            return self.llm_client(prompt)

        raise RuntimeError(
            "LLM client no expone interfaz soportada. "
            "Se espera .generate(payload|prompt), .complete(prompt) o callable(prompt)."
        )

    # ==================================================
    # Parse helper
    # ==================================================
    def _safe_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        try:
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    # ==================================================
    # Interpretation handler
    # ==================================================
    def _handle_interpretation(
        self,
        state: K9State,
        parsed: Optional[Dict[str, Any]],
        raw_response: str,
    ) -> K9State:
        if parsed is None:
            log_clarification_event(
                state=state,
                reason="LLM returned non-JSON during interpretation",
            )
            state.answer = "No fue posible interpretar la solicitud de forma canónica."
            return state

        # Bootstrap ultra-simple (para destrabar smoke01)
        if self._is_simple_question(state.user_query):
            if parsed.get("type") != "K9_COMMAND":
                log_clarification_event(
                    state=state,
                    reason="Invalid response for simple question (expected K9_COMMAND)",
                )
                state.answer = "No fue posible interpretar la solicitud."
                return state

            state.context_bundle = {"k9_command": parsed}
            state.answer = None
            return state

        # Contrato completo
        ok, reason = validate_llm_output_schema(parsed)
        if not ok:
            log_clarification_event(state=state, reason=reason)
            state.answer = "No fue posible interpretar la solicitud de forma canónica."
            return state

        if parsed.get("type") == "CLARIFICATION_REQUEST":
            log_clarification_event(state=state, reason="LLM requested clarification")
            state.answer = "Necesito un poco más de precisión para continuar."
            return state

        state.context_bundle = {"k9_command": parsed}
        state.answer = None
        return state

    # ==================================================
    # Synthesis handler
    # ==================================================
    def _handle_synthesis(
        self,
        state: K9State,
        parsed: Optional[Dict[str, Any]],
        raw_response: str,
    ) -> K9State:
        # Si el LLM no devolvió JSON, devolvemos raw (fail-soft en salida)
        if parsed is None:
            state.answer = raw_response
            return state

        if parsed.get("type") != "FINAL_ANSWER":
            state.answer = raw_response
            return state

        answer = parsed.get("answer")

        # Contrato final: siempre string
        if isinstance(answer, str):
            state.answer = answer
        else:
            state.answer = json.dumps(answer, ensure_ascii=False, indent=2)

        return state

    # ==================================================
    # Payload builder
    # ==================================================
    def _build_payload(self, state: K9State, phase: str) -> LLMPayload:
        system = LLMSystemContract()

        user = LLMUserContext(
            original_question=state.user_query,
            language="es",
            turn_index=getattr(state, "turn_index", 0),
        )

        command = state.context_bundle.get("k9_command", {}) if state.context_bundle else {}

        # 🔒 Synthesis contract: el LLMNode NO debe distorsionar el estado K9.
        # Se propaga exactamente lo que el sistema produjo, sin defaults forzados.

        k9 = LLMK9Context(
            k9_command=command,
            narrative_context=state.narrative_context,   # opcional, sin "{}"
            operational_analysis=state.analysis,         # fuente determinista
            analyst_results=state.analysis,              # placeholder coherente (si aplica)
        )

        instruction = (
            "PROMPT_V0_SIMPLE"
            if phase == "interpretation" and self._is_simple_question(state.user_query)
            else phase.upper()
        )

        session_id = (
            state.llm_session_context.session_id
            if state.llm_session_context is not None
            else f"smoke-{uuid.uuid4().hex[:8]}"
        )

        return LLMPayload(
            system=system,
            session_id=session_id,
            active_phase=phase,
            is_composite=False,
            user=user,
            k9=k9,
            knowledge=self.knowledge_scaffold,
            instruction=instruction,
        )

    # ==================================================
    # Phase resolver
    # ==================================================
    def _resolve_phase(self, state: K9State) -> str:
        if state.llm_session_context is None:
            return "interpretation"
        return state.llm_session_context.active_phase

    # ==================================================
    # Bootstrap detector
    # ==================================================
    def _is_simple_question(self, question: str) -> bool:
        q = (question or "").lower()
        return ("cuántas observaciones" in q) and ("última semana" in q)
