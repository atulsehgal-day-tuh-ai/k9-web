from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import json

# Prompt builders (infraestructura lingüística)
from src.llm.prompts import (
    build_prompt_human_to_k9,
    build_prompt_k9_to_human,
)


# =====================================================
# SYSTEM CONTRACT
# =====================================================

class LLMSystemContract(BaseModel):
    """
    Contrato explícito del rol del LLM dentro de K9.
    Esto se convierte en el system prompt.
    """
    role: str = "linguistic_interface"
    constraints: List[str] = Field(default_factory=lambda: [
        "do_not_reason",
        "do_not_decide_flow",
        "do_not_create_new_entities",
        "do_not_infer_missing_data",
        "follow_k9_semantic_schema",
        "explain_only_what_is_provided",
    ])


# =====================================================
# USER CONTEXT
# =====================================================

class LLMUserContext(BaseModel):
    """
    Contexto del usuario (NO interpretado).
    """
    original_question: str
    normalized_question: Optional[str] = None
    language: str = "es"
    turn_index: int


# =====================================================
# K9 CONTEXT
# =====================================================

class LLMK9Context(BaseModel):
    """
    Contexto estructural producido por K9 (fuente de verdad).
    """
    k9_command: Dict[str, Any]

    # Resultados del core (solo lectura)
    operational_analysis: Optional[Dict[str, Any]] = None
    analyst_results: Optional[Dict[str, Any]] = None

    # Andamiaje narrativo (opcional)
    narrative_context: Optional[Dict[str, Any]] = None

    # Para preguntas compuestas
    partial_results: Optional[List[Dict[str, Any]]] = None


# =====================================================
# KNOWLEDGE SCAFFOLD
# =====================================================

class LLMKnowledgeScaffold(BaseModel):
    """
    Andamiaje cognitivo que el LLM debe respetar.
    """

    canonical_schema: Dict[str, Any]
    domain_semantics: Dict[str, Any]

    # NOTE: These are structured JSON bundles loaded from `src/language/*`.
    canonical_language: Dict[str, Any]
    examples_basic: Optional[Any] = None
    examples_advanced: Optional[Any] = None
    meta_reasoning_examples: Optional[Any] = None


# =====================================================
# PAYLOAD
# =====================================================

class LLMPayload(BaseModel):
    """
    LLMPayload — K9 v1.0

    Payload COMPLETO y AUTOSUFICIENTE para una llamada LLM.
    """

    # 1. Contrato del sistema
    system: LLMSystemContract

    # 2. Contexto de sesión
    session_id: str
    active_phase: str
    is_composite: bool

    # 3. Contexto del usuario
    user: LLMUserContext

    # 4. Contexto K9
    k9: LLMK9Context

    # 5. Andamiaje semántico
    knowledge: LLMKnowledgeScaffold

    # 6. Instrucción final (reservado)
    instruction: str

    # =====================================================
    # PROMPT RENDERING (ÚNICO PUNTO DE ENTRADA)
    # =====================================================
    def render(self) -> str:
        """
        Renderiza el payload a texto según la fase activa.

        🔒 ÚNICO lugar donde se construyen prompts.
        🔒 El cliente LLM NO conoce estructura interna.
        """

        phase = self.active_phase

        # -------------------------------------------------
        # NL → K9 (interpretation)
        # -------------------------------------------------
        if phase == "interpretation":
            return build_prompt_human_to_k9(
                user_query=self.user.original_question,
                bundle={
                    "schema": self.knowledge.canonical_schema,
                    "language": self.knowledge.canonical_language,
                    "domain_semantics_es": self.knowledge.domain_semantics,
                    "examples_basic": self.knowledge.examples_basic or [],
                    "examples_advanced": self.knowledge.examples_advanced or [],
                    "meta_reasoning_examples": self.knowledge.meta_reasoning_examples or [],
                },
            )

        # -------------------------------------------------
        # K9 → NL (synthesis)
        # -------------------------------------------------
        if phase == "synthesis":

            synthesis_envelope: Dict[str, Any] = {
                "original_question": self.user.original_question,
                "intent": self.k9.k9_command.get("intent"),
                "k9_command": self.k9.k9_command,
                "operational_analysis": self.k9.operational_analysis,
                "analyst_results": self.k9.analyst_results,
                "narrative_context": self.k9.narrative_context,
                "partial_results": self.k9.partial_results,
                "is_composite": self.is_composite,
            }

            return build_prompt_k9_to_human(
                original_question=self.user.original_question,
                synthesis_input=json.dumps(
                    synthesis_envelope,
                    ensure_ascii=False,
                    indent=2,
                ),
            )

        # -------------------------------------------------
        # Safety net
        # -------------------------------------------------
        raise ValueError(f"Unsupported LLM phase: {phase}")
