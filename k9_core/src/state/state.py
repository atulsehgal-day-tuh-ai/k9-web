from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Infraestructura LLM (NO cognición)
from src.llm.session_context import LLMSessionContext

# 🔒 Contratos temporales explícitos
from src.time.time_context import TimeContext
from src.time.data_slice import DataSlice


class K9State(BaseModel):
    # ==================================================
    # INPUTS (infraestructura, no cognición)
    # ==================================================

    # Pregunta original del usuario (solo trazabilidad)
    user_query: str = ""

    # Comando canónico K9 (FUENTE DE VERDAD DEL GRAFO)
    k9_command: Optional[Dict[str, Any]] = None

    # ==================================================
    # TRAZABILIDAD DE EJECUCIÓN
    # ==================================================
    reasoning: List[str] = Field(default_factory=list)

    # ==================================================
    # FLAGS DE EJECUCIÓN
    # ==================================================
    demo_mode: bool = False

    # ==================================================
    # CONTEXTO ESTRUCTURAL
    # ==================================================
    context_bundle: Optional[Dict[str, Any]] = None

    # ==================================================
    # ⏱️ CONTEXTO TEMPORAL CANÓNICO (NUEVO)
    # ==================================================

    # Resultado de traducir payload.time → TimeContext
    time_context: Optional[TimeContext] = None

    # Corte físico de datos derivado del TimeContext
    data_slice: Optional[DataSlice] = None

    # ==================================================
    # DECISIÓN OPERACIONAL (CORE)
    # ==================================================
    intent: Optional[str] = None

    # ==================================================
    # SEÑALES TEMPORALES / STDE
    # ==================================================
    signals: Optional[Dict[str, Any]] = None

    # Evento activo (ej. lunes crítico)
    active_event: Optional[Dict[str, Any]] = None

    # ==================================================
    # ANÁLISIS COGNITIVO
    # ==================================================
    analysis: Optional[Dict[str, Any]] = None

    # Enriquecimiento operacional (OCC, controles, etc.)
    risk_enrichment: Optional[Dict[str, Any]] = None

    # ==================================================
    # CONTEXTO NARRATIVO (PRE-LLM)
    # ==================================================
    narrative_context: Optional[Dict[str, Any]] = None

    # ==================================================
    # LLM SESSION (INFRAESTRUCTURA)
    # ==================================================
    llm_session_context: Optional[LLMSessionContext] = None

    # ==================================================
    # SALIDA FINAL
    # ==================================================
    answer: Optional[str] = None
