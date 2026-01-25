from src.state.state import K9State

# 🔒 Contrato temporal canónico
from src.time.time_context import TimeContext


# -----------------------------
# K9 Canonical Intent Space
# -----------------------------
VALID_INTENTS = {
    "GREETING_QUERY",
    "ONTOLOGY_QUERY",
    "OPERATIONAL_QUERY",
    "ANALYTICAL_QUERY",
    "COMPARATIVE_QUERY",
    "TEMPORAL_RELATION_QUERY",
    "SYSTEM_QUERY",
}

# Tipos de comando soportados por el router
VALID_COMMAND_TYPES = {
    "K9_COMMAND",
    "COMPOSITE_K9_COMMAND",
}

# Intent → mundo cognitivo / nodo esperado (trazabilidad)
INTENT_TARGET_MAP = {
    "GREETING_QUERY": "NarrativeNode",
    "ONTOLOGY_QUERY": "OntologyQueryNode",
    "OPERATIONAL_QUERY": "OperationalAnalysisNode",
    "ANALYTICAL_QUERY": "AnalystNode",
    "COMPARATIVE_QUERY": "AnalystNode",
    "TEMPORAL_RELATION_QUERY": "AnalystNode",
    "SYSTEM_QUERY": "OperationalAnalysisNode",
}

# -----------------------------
# Vocabulario canónico de tiempo
# -----------------------------
VALID_TIME_VALUES = {
    "RELATIVE": {
        "CURRENT_WEEK",
        "LAST_WEEK",
        "LAST_2_WEEKS",
        "LAST_4_WEEKS",
        "LAST_MONTH",
    },
    "WINDOW": {
        "PRE",
        "POST",
        "PRE_POST",
    },
    "ANCHOR": {
        "CRITICAL_MONDAY",
    },
}


def router_node(state: K9State) -> K9State:
    """
    Router Node — K9 Canonical (v1.4)

    Rol:
    - Validar comandos K9 explícitos
    - Registrar trazabilidad cognitiva
    - Traducir payload.time → TimeContext
    - NO resolver rangos temporales
    - NO filtrar datos
    - NO ejecutar planes compuestos

    Fuente única de verdad:
    - state.k9_command
    Compatibilidad:
    - state.context_bundle["k9_command"] se mantiene para nodos legacy.
    """

    context = state.context_bundle or {}
    command = state.k9_command or context.get("k9_command")

    if not command:
        raise ValueError(
            "RouterNode error: missing k9_command."
        )

    # Canonicalize storage for downstream nodes
    state.k9_command = command
    context["k9_command"] = command
    state.context_bundle = context

    command_type = command.get("type", "K9_COMMAND")

    # -----------------------------
    # Validación de tipo de comando
    # -----------------------------
    if command_type not in VALID_COMMAND_TYPES:
        raise ValueError(
            f"RouterNode ERROR: invalid command type '{command_type}'. "
            f"Allowed={sorted(VALID_COMMAND_TYPES)}"
        )

    # =========================================================
    # CASO 1 — COMPOSITE_K9_COMMAND
    # =========================================================
    if command_type == "COMPOSITE_K9_COMMAND":
        state.intent = "COMPOSITE_PLAN"
        context["composite_plan"] = command

        state.reasoning.append(
            "RouterNode: COMPOSITE_K9_COMMAND detected. "
            "Execution deferred (cognitive plan)."
        )
        return state

    # =========================================================
    # CASO 2 — K9_COMMAND simple
    # =========================================================
    intent = command.get("intent")
    entity = command.get("entity")
    operation = command.get("operation")

    if intent not in VALID_INTENTS:
        raise ValueError(
            f"RouterNode ERROR: invalid intent '{intent}'. "
            f"Allowed={sorted(VALID_INTENTS)}"
        )

    target_node = INTENT_TARGET_MAP.get(intent, "UNKNOWN")

    state.reasoning.append(
        f"RouterNode: intent '{intent}' validated "
        f"(entity={entity}, operation={operation}) "
        f"→ expected target={target_node}."
    )

    # =========================================================
    # 🔑 Traducción payload.time → TimeContext
    # =========================================================
    payload = command.get("payload", {}) or {}
    payload_time = payload.get("time")

    # ---------
    # DEFAULT EXPLÍCITO
    # ---------
    if payload_time is None:
        state.time_context = TimeContext(
            type="RELATIVE",
            value="CURRENT_WEEK",
            confidence="INFERRED",
        )

        state.reasoning.append(
            "RouterNode: no payload.time provided → "
            "default TimeContext CURRENT_WEEK (INFERRED)."
        )

    else:
        time_type_raw = payload_time.get("type")
        time_value_raw = payload_time.get("value")
        confidence = payload_time.get("confidence", "EXPLICIT")

        # Validación básica de tipos
        if not isinstance(time_type_raw, str) or not isinstance(time_value_raw, str):
            raise ValueError(
                "RouterNode ERROR: payload.time.type and payload.time.value must be strings."
            )

        # 🔒 Canonicalización de casing (LLM → core)
        time_type = time_type_raw.upper()
        time_value = time_value_raw.upper()

        # 🔒 Normalización semántica mínima
        # Caso típico del LLM: WINDOW + LAST_*  → RELATIVE
        if time_type == "WINDOW" and time_value.startswith("LAST_"):
            state.reasoning.append(
                f"RouterNode: correcting time.type from WINDOW to RELATIVE "
                f"for value '{time_value}'."
            )
            time_type = "RELATIVE"

        # Validación estricta contra vocabulario canónico
        if time_type not in VALID_TIME_VALUES:
            raise ValueError(
                f"RouterNode ERROR: invalid time.type '{time_type_raw}'. "
                f"Allowed={sorted(VALID_TIME_VALUES.keys())}"
            )

        if time_value not in VALID_TIME_VALUES[time_type]:
            raise ValueError(
                f"RouterNode ERROR: invalid time.value '{time_value_raw}' "
                f"for type '{time_type}'. "
                f"Allowed={sorted(VALID_TIME_VALUES[time_type])}"
            )

        state.time_context = TimeContext(
            type=time_type,
            value=time_value,
            confidence=confidence,
        )

        state.reasoning.append(
            f"RouterNode: TimeContext created "
            f"(type={time_type}, value={time_value}, confidence={confidence})."
        )

    # -----------------------------
    # Compatibilidad legacy
    # -----------------------------
    # state.intent NO es fuente de verdad,
    # se mantiene solo para nodos/tests legacy
    state.intent = intent

    return state
