from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class PartialResponse(BaseModel):
    """
    Resultado parcial de una sub-pregunta dentro de un COMPOSITE_COMMAND.

    ❗ sub_command_id debe ser único dentro de la sesión
       (por ejemplo: 'step_1', 'step_2' o UUID corto).
    ❗ Nunca se muestra directamente al usuario.
    ❗ Solo se usa como insumo para la fase de síntesis.
    """
    sub_command_id: str
    intent: str
    entity: Optional[str] = None
    operation: Optional[str] = None

    narrative_context: Dict[str, Any]
    answer_partial: str


class LLMSessionContext(BaseModel):
    """
    LLMSessionContext — K9 v1.0

    Memoria conversacional CURADA para el LLM.
    No es memoria libre, no es chat history.

    El LLM:
      - NO escribe aquí
      - NO interpreta esta estructura
      - SOLO la consume cuando el sistema la expone
    """

    # =====================================================
    # Identidad de sesión
    # =====================================================
    session_id: str
    turn_index: int = 0

    # =====================================================
    # Historia controlada
    # =====================================================
    user_questions: List[str] = Field(default_factory=list)
    k9_commands: List[Dict[str, Any]] = Field(default_factory=list)

    narrative_contexts: List[Dict[str, Any]] = Field(default_factory=list)

    # =====================================================
    # Manejo de preguntas compuestas
    # =====================================================
    partial_responses: List[PartialResponse] = Field(default_factory=list)

    active_composite: bool = False
    active_phase: Optional[str] = None
    # Valores esperados:
    # - "interpretation"
    # - "synthesis"

    # =====================================================
    # Salidas finales previas
    # =====================================================
    final_answers: List[str] = Field(default_factory=list)

    # =====================================================
    # Utilidades de control (no semánticas)
    # =====================================================
    meta: Dict[str, Any] = Field(default_factory=dict)

    # =====================================================
    # Helpers explícitos (opcionales, no mágicos)
    # =====================================================
    def register_turn(self, user_question: str, k9_command: Dict[str, Any]) -> None:
        """
        Registra una nueva interacción del usuario.
        """
        self.turn_index += 1
        self.user_questions.append(user_question)
        self.k9_commands.append(k9_command)

    def register_narrative_context(self, narrative_context: Dict[str, Any]) -> None:
        """
        Registra el contexto narrativo usado para una llamada LLM.
        """
        self.narrative_contexts.append(narrative_context)

    def register_partial_response(self, response: PartialResponse) -> None:
        """
        Agrega una respuesta parcial (solo COMPOSITE).
        """
        self.partial_responses.append(response)

    def register_final_answer(self, answer: str) -> None:
        """
        Registra una respuesta final emitida al usuario.
        """
        self.final_answers.append(answer)
        self.active_phase = None
        self.active_composite = False

    def register_clarification(self, clarification: Dict[str, Any]) -> None:
        """
        Registra una solicitud de clarificación ocurrida en esta sesión.

        ⚠️ No es persistencia global.
        ⚠️ Se usa solo como trazabilidad in-session.
        """
        if "clarifications" not in self.meta:
            self.meta["clarifications"] = []
        self.meta["clarifications"].append(clarification)

    @classmethod
    def create(cls) -> "LLMSessionContext":
        return cls(
            session_id=f"llm-{uuid.uuid4().hex[:12]}"
        )
