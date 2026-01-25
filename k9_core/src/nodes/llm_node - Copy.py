from __future__ import annotations

from typing import Any, Dict

from src.state.state import K9State

from src.llm.base_client import BaseLLMClient
from src.llm.session_context import LLMSessionContext, PartialResponse
from src.llm.payload import (
    LLMPayload,
    LLMSystemContract,
    LLMUserContext,
    LLMK9Context,
    LLMKnowledgeScaffold,
)

from src.llm.language_bundle import load_k9_language_bundle
from src.llm.prompts import (
    build_prompt_human_to_k9,
    build_prompt_k9_to_human,
)
from src.llm.json_utils import extract_json_object, safe_json_loads
from src.llm.validators import (
    validate_llm_output_schema,
    validate_composite_llm_output_schema,
)


class LLMNode:
    """
    LLMNode — K9 v1.0 (orquestador lingüístico)

    - NO razona
    - NO decide flujo
    - NO ejecuta lógica cognitiva
    - SOLO orquesta interacción entre:
        K9State ↔ Payload ↔ LLMClient
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        knowledge_scaffold: LLMKnowledgeScaffold,
    ):
        self.llm_client = llm_client
        self.knowledge = knowledge_scaffold

    # =====================================================
    # Entry point (LangGraph)
    # =====================================================
    def __call__(self, state: K9State) -> K9State:

        if state.context_bundle is None:
            state.context_bundle = {}

        # -------------------------------------------------
        # 1. Inicializar / recuperar sesión LLM
        # -------------------------------------------------
        if state.llm_session_context is None:
            state.llm_session_context = LLMSessionContext.create()

        session = state.llm_session_context

        if session.active_phase != "interpretation" and state.narrative_context is not None:
            session.register_narrative_context(state.narrative_context)

        # -------------------------------------------------
        # 2. Registrar turno (solo una vez por pregunta)
        # -------------------------------------------------
        if session.turn_index == 0 or (
            not session.user_questions
            or session.user_questions[-1] != state.user_query
        ):
            session.register_turn(
                user_question=state.user_query,
                k9_command=state.context_bundle.get("k9_command", {}),
            )

        # -------------------------------------------------
        # 3. Determinar fase (controlada por el sistema)
        # -------------------------------------------------
        if session.active_phase:
            phase = session.active_phase
        elif "k9_command" not in state.context_bundle:
            phase = "interpretation"
        else:
            phase = "synthesis"

        is_composite = session.active_composite

        # -------------------------------------------------
        # 4. Construir payload
        # -------------------------------------------------
        payload = self._build_payload(
            state=state,
            session=session,
            phase=phase,
            is_composite=is_composite,
        )

        # -------------------------------------------------
        # 5. Ejecutar cliente LLM
        # -------------------------------------------------
        raw_output = self.llm_client.generate(payload)

        # -------------------------------------------------
        # 6. Manejo por fase
        # -------------------------------------------------
        if phase == "interpretation":
            self._handle_interpretation(state, raw_output)
            return state

        if phase == "explanation_i":
            self._handle_partial_explanation(state, raw_output)

            # 🔒 INVARIANTE CRÍTICA:
            # En explanation_i NUNCA se escribe answer
            state.answer = None
            return state

        if phase == "synthesis":
            session.register_final_answer(raw_output)
            state.answer = raw_output
            return state

        raise ValueError(f"Unknown LLM phase: {phase}")

    # =====================================================
    # Payload builder
    # =====================================================
    def _build_payload(
        self,
        state: K9State,
        session: LLMSessionContext,
        phase: str,
        is_composite: bool,
    ) -> LLMPayload:
        user_ctx = LLMUserContext(
            original_question=state.user_query,
            turn_index=session.turn_index,
        )

        # -------------------------------------------------
        # K9 command (interpretation-safe)
        # -------------------------------------------------
        k9_command = (
            state.context_bundle.get("k9_command")
            if phase != "interpretation"
            else {}
        )

        # -------------------------------------------------
        # Narrative context
        # -------------------------------------------------
        narrative_ctx = (
            state.narrative_context
            if state.narrative_context is not None
            else {}
        )

        k9_ctx = LLMK9Context(
            k9_command=k9_command,
            narrative_context=narrative_ctx,
            operational_analysis=state.analysis,
            analyst_results={"reasoning": state.reasoning},
            partial_results=[
                pr.model_dump() for pr in session.partial_responses
            ] if session.partial_responses else None,
        )

        return LLMPayload(
            system=LLMSystemContract(),
            session_id=session.session_id,
            active_phase=phase,
            is_composite=is_composite,
            user=user_ctx,
            k9=k9_ctx,
            knowledge=self.knowledge,
            instruction=self._instruction_for_phase(phase),
        )

    # =====================================================
    # Phase handlers
    # =====================================================
    def _handle_interpretation(self, state: K9State, raw_text: str) -> None:
        """
        NL → K9 translation (fail-closed).
        """
        raw_json = extract_json_object(raw_text)
        if not raw_json:
            self._fail_closed(state, "LLM did not return JSON.")
            return

        parsed, err = safe_json_loads(raw_json)
        if not parsed:
            self._fail_closed(state, f"Invalid JSON: {err}")
            return

        out_type = parsed.get("type")

        if out_type == "K9_COMMAND":
            ok, msg = validate_llm_output_schema(parsed)
            if not ok:
                self._fail_closed(state, msg)
                return

            state.context_bundle["k9_command"] = parsed["payload"]

            # LEGACY — intent ya no es parte de K9State
            # state.intent = parsed["payload"].get("intent")

            return

        if out_type == "COMPOSITE_K9_COMMAND":
            ok, msg = validate_composite_llm_output_schema(parsed)
            if not ok:
                self._fail_closed(state, msg)
                return

            normalized_plan = []

            for step in parsed["plan"]:
                payload = step.get("payload", {})

                normalized_plan.append({
                    "type": "K9_COMMAND",
                    "intent": payload.get("intent"),
                    "entity": payload.get("entity"),
                    "operation": payload.get("operation"),
                    "output": payload.get("output"),
                })

            state.context_bundle["k9_command"] = {
                "type": "COMPOSITE_K9_COMMAND",
                "plan": normalized_plan,
            }

            session = state.llm_session_context
            session.active_composite = True

            # LEGACY — intent ya no es parte de K9State
            # state.intent = "COMPOSITE_QUERY"

            return

        if out_type == "CLARIFICATION_REQUEST":
            state.answer = self._render_clarification(parsed)

            # LEGACY — intent ya no es parte de K9State
            # state.intent = "CLARIFICATION_REQUEST"

            return

        self._fail_closed(state, f"Unknown LLM output type: {out_type}")

    def _handle_partial_explanation(self, state: K9State, text: str) -> None:
        """
        Guarda explicación parcial (COMPOSITE).
        """
        session = state.llm_session_context

        step_idx = session.meta.get("active_step_index", 0)

        composite = state.context_bundle.get("k9_command", {})
        plan = composite.get("plan", [])

        if not plan or step_idx >= len(plan):
            raise ValueError("Invalid COMPOSITE state: no active sub-command available")

        sub_cmd = plan[step_idx]

        pr = PartialResponse(
            sub_command_id=str(step_idx + 1),
            intent=sub_cmd.get("intent"),
            entity=sub_cmd.get("entity"),
            operation=sub_cmd.get("operation"),
            narrative_context=state.narrative_context or {},
            answer_partial=text,
        )

        session.register_partial_response(pr)

        session.meta["active_step_index"] = step_idx + 1

    # =====================================================
    # Helpers
    # =====================================================
    def _instruction_for_phase(self, phase: str) -> str:
        if phase == "interpretation":
            return "Translate the user request into a canonical K9 command. Return only valid JSON."

        if phase == "explanation_i":
            return "Explain this sub-result exactly as provided, without synthesis."

        if phase == "synthesis":
            return "Synthesize all validated partial explanations into one coherent answer."

        raise ValueError(f"Unknown LLM phase: {phase}")

    def _render_clarification(self, obj: Dict[str, Any]) -> str:
        options = obj.get("options", [])
        lines = ["Necesito un poco más de precisión para continuar:"]
        for i, opt in enumerate(options, start=1):
            lines.append(f"{i}. {opt.get('label')}: {opt.get('description')}")
        return "\n".join(lines)

    def _fail_closed(self, state: K9State, reason: str) -> None:
        """
        Fail-closed determinista: nunca inventa.
        """
        state.answer = (
            "No fue posible interpretar la solicitud de forma canónica. "
            "Por favor, reformule o entregue mayor precisión."
        )

        # LEGACY — intent ya no es parte de K9State
        # state.intent = "CLARIFICATION_REQUEST"

        state.reasoning.append(f"LLMNode fail-closed: {reason}")
