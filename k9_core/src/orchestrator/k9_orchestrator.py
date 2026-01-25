# src/orchestrator/k9_orchestrator.py
from __future__ import annotations

from typing import Dict, Any

from src.state.state import K9State
from src.llm.session_context import (
    LLMSessionContext,
    PartialResponse,
)
from src.llm.payload import LLMPayload
from src.llm.validators import (
    validate_llm_output_schema,
    validate_composite_llm_output_schema,
)
from src.llm.clarification_log import ClarificationLog
from src.graph.build_graph import build_k9_graph
from src.llm.contract import LLMSystemContract  # o donde esté definido


class K9Orchestrator:
    """
    Orquestador general del sistema K9.

    Responsabilidades:
    - NL → K9 (interpretation)
    - Manejo de clarifications (persistentes)
    - Ejecución de comandos simples
    - Ejecución de comandos compuestos
    - Ejecución del grafo cognitivo K9
    - K9 → NL (synthesis)

    El grafo NO decide flujo lingüístico.
    El LLM NO decide cognición.
    """

    def __init__(self, llm_client, knowledge_bundle):
        self.llm = llm_client
        self.knowledge = knowledge_bundle
        self.graph = build_k9_graph()
        self.clarification_log = ClarificationLog()

        # Contrato explícito del LLM
        self.system_contract = LLMSystemContract()

    # ==================================================
    # ENTRY POINT
    # ==================================================
    def handle_user_query(self, user_query: str) -> str:
        session = LLMSessionContext.create()

        # ==================================================
        # 1. NL → K9 (INTERPRETATION)
        # ==================================================
        interpretation_payload = LLMPayload(
            system=self.system_contract,
            session_id=session.session_id,
            active_phase="interpretation",
            is_composite=False,
            user={
                "original_question": user_query,
                "turn_index": session.turn_index,
            },
            k9={
                "k9_command": {},
                "narrative_context": {},
            },
            knowledge=self.knowledge,
            instruction="Translate NL to K9 command",
        )

        raw_llm_output = self.llm.invoke(
            interpretation_payload.render()
        )

        parsed: Dict[str, Any] = raw_llm_output  # ya parseado a dict

        # ==================================================
        # 2. VALIDACIÓN ESTRUCTURAL
        # ==================================================
        if parsed.get("type") == "COMPOSITE_K9_COMMAND":
            ok, msg = validate_composite_llm_output_schema(parsed)
        else:
            ok, msg = validate_llm_output_schema(parsed)

        if not ok:
            raise ValueError(f"Invalid LLM output: {msg}")

        # ==================================================
        # 3. CLARIFICATION
        # ==================================================
        if parsed["type"] == "CLARIFICATION_REQUEST":
            self.clarification_log.record(
                session_id=session.session_id,
                turn_index=session.turn_index,
                user_question=user_query,
                reason=parsed.get("reason"),
                options=parsed.get("options"),
                raw_llm_output=parsed,
            )
            return self._render_clarification(parsed)

        # ==================================================
        # 4. COMPOSITE COMMAND
        # ==================================================
        if parsed["type"] == "COMPOSITE_K9_COMMAND":
            return self._execute_composite(parsed, session, user_query)

        # ==================================================
        # 5. SINGLE COMMAND
        # ==================================================
        if parsed["type"] == "K9_COMMAND":
            return self._execute_single(parsed, session, user_query)

        # Safety net (no debería ocurrir)
        return "No se pudo interpretar la consulta."

    # ==================================================
    # EJECUCIÓN SINGLE
    # ==================================================
    def _execute_single(
        self,
        command: Dict[str, Any],
        session: LLMSessionContext,
        user_query: str,
    ) -> str:

        # ✅ Registro del turno
        session.register_turn(user_query, command)

        state = K9State(
            user_query=user_query,
            k9_command=command,
            llm_session_context=session,
        )

        result = self.graph.invoke(state)

        # ✅ Registro de contexto narrativo
        if result.narrative_context:
            session.register_narrative_context(result.narrative_context)

        # ==================================================
        # SÍNTESIS K9 → NL
        # ==================================================
        synthesis_payload = LLMPayload(
            system=self.system_contract,
            session_id=session.session_id,
            active_phase="synthesis",
            is_composite=False,
            user={},
            k9={
                "k9_command": command,
                "narrative_context": result.narrative_context,
            },
            knowledge=self.knowledge,
            instruction="Translate K9 narrative to Spanish",
        )

        final = self.llm.invoke(
            synthesis_payload.render()
        )

        # ✅ Registro de respuesta final
        session.register_final_answer(final["answer"])

        return final["answer"]

    # ==================================================
    # EJECUCIÓN COMPOSITE
    # ==================================================
    def _execute_composite(
        self,
        composite: Dict[str, Any],
        session: LLMSessionContext,
        user_query: str,
    ) -> str:

        session.active_composite = True

        for idx, step in enumerate(composite["plan"], start=1):
            step_id = f"step_{idx}"

            # ✅ Registro de cada sub-turno
            session.register_turn(user_query, step)

            state = K9State(
                user_query=user_query,
                k9_command=step,
                llm_session_context=session,
            )

            result = self.graph.invoke(state)

            # ✅ Registro de respuesta parcial estructurada
            session.register_partial_response(
                PartialResponse(
                    sub_command_id=step_id,
                    intent=step.get("intent"),
                    entity=step.get("payload", {}).get("entity"),
                    operation=step.get("payload", {}).get("operation"),
                    narrative_context=result.narrative_context or {},
                    answer_partial="",
                )
            )

        # ==================================================
        # SÍNTESIS FINAL COMPOSITE
        # ==================================================
        synthesis_payload = LLMPayload(
            system=self.system_contract,
            session_id=session.session_id,
            active_phase="synthesis",
            is_composite=True,
            user={},
            k9={
                "k9_command": composite,
                "narrative_context": {
                    "partials": [
                        pr.narrative_context
                        for pr in session.partial_responses
                    ]
                },
            },
            knowledge=self.knowledge,
            instruction="Synthesize composite answer",
        )

        final = self.llm.invoke(
            synthesis_payload.render()
        )

        # ✅ Registro de respuesta final
        session.register_final_answer(final["answer"])

        return final["answer"]

    # ==================================================
    # RENDER CLARIFICATION
    # ==================================================
    def _render_clarification(self, parsed: Dict[str, Any]) -> str:
        opts = "\n".join(
            f"- {o['label']}: {o['description']}"
            for o in parsed.get("options", [])
        )
        return f"{parsed['reason']}\n\nOpciones:\n{opts}"
