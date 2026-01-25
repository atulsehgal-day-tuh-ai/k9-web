# src/nodes/narrative_node.py

from src.state.state import K9State


# =====================================================
# Helpers semánticos (NO razonan, NO generan texto)
# =====================================================

def _infer_narrative_intent(intent: str, operation: str | None) -> str:
    """
    Meta-intención explicativa para el LLM.
    No es intent canónico, no decide flujo.
    """
    if intent == "ANALYTICAL_QUERY":
        if operation == "compare":
            return "model_comparison_explanation"
        return "analytical_status_explanation"

    if intent == "COMPARATIVE_QUERY":
        return "comparative_explanation"

    if intent == "TEMPORAL_RELATION_QUERY":
        return "temporal_evolution_explanation"

    if intent == "ONTOLOGY_QUERY":
        return "ontology_definition"

    if intent == "OPERATIONAL_QUERY":
        return "factual_summary"

    if intent == "GREETING_QUERY":
        return "institutional_intro"

    return "generic_explanation"


def _infer_conceptual_axes(intent: str, entity: str | None) -> list[str]:
    """
    Ejes conceptuales sugeridos para estructurar la explicación.
    No son frases ni conclusiones.
    """
    axes: list[str] = []

    if intent in {"ANALYTICAL_QUERY", "COMPARATIVE_QUERY"}:
        axes.extend([
            "trend_vs_snapshot",
            "signal_accumulation",
            "operational_pressure",
        ])

    if intent == "COMPARATIVE_QUERY":
        axes.append("model_blind_spots")

    if intent == "TEMPORAL_RELATION_QUERY":
        axes.append("before_after_relation")

    if intent == "ONTOLOGY_QUERY":
        axes.append("structural_definition")

    if entity in {"risk", "risks"}:
        axes.append("severity_vs_frequency")

    return axes


def _default_narrative_constraints() -> list[str]:
    """
    Guardrails semánticos suaves para el LLM.
    """
    return [
        "do_not_recommend_actions",
        "do_not_assign_blame",
        "do_not_infer_missing_data",
        "do_not_explain_outside_time_window",
        "do_not_create_new_entities",
    ]


# =====================================================
# Narrative Node
# =====================================================

def narrative_node(state: K9State) -> K9State:
    """
    NarrativeNode — K9 v3.4 (Cognitive, pre-LLM)

    Rol:
    - Construir CONTEXTO NARRATIVO ESTRUCTURADO para el LLM
    - Curaduría semántica (no razonamiento)
    - Andamiaje cognitivo, no respuesta humana

    NO hace:
    - No consulta datos
    - No razona
    - No genera texto final
    - No infiere intención
    """

    command = state.k9_command or (state.context_bundle or {}).get("k9_command")

    # =====================================================
    # 0. GATING DURO — solo si el comando lo pide
    # =====================================================
    if not command:
        state.reasoning.append(
            "NarrativeNode: skipped (no k9_command)."
        )
        return state

    # Output can live either at the top-level (preferred for nodes) or inside payload (validator enforces payload.output)
    output = command.get("output") or (command.get("payload", {}) or {}).get("output")
    if output != "narrative":
        state.reasoning.append(
            f"NarrativeNode: skipped (output={output})."
        )
        return state

    intent = command.get("intent")
    operation = command.get("operation")
    entity = command.get("entity")
    is_composite = command.get("type") == "COMPOSITE_K9_COMMAND"

    # =====================================================
    # 1. Inicializar contexto narrativo
    # =====================================================
    narrative_context = {
        # Capa 1 — tipo narrativo
        "narrative_type": None,

        # Capa 2 — intención explicativa
        "narrative_intent": None,

        # Capa 3 — ejes conceptuales
        "conceptual_axes": [],

        # Guardrails semánticos
        "narrative_constraints": [],

        # Evidencia estructurada
        "semantic_focus": [],
        "key_entities": [],
        "key_risks": [],
        "signals": [],
        "comparisons": [],
        "temporal_markers": [],

        # Ayuda directa al LLM
        "notes_for_llm": [],
    }

    # =====================================================
    # 2. Determinar tipo de narrativa (NO contenido)
    # =====================================================
    if is_composite:
        narrative_context["narrative_type"] = "composite"
    elif intent == "OPERATIONAL_QUERY":
        narrative_context["narrative_type"] = "operational"
    elif intent in {"ANALYTICAL_QUERY", "TEMPORAL_RELATION_QUERY"}:
        narrative_context["narrative_type"] = "analytical"
    elif intent == "COMPARATIVE_QUERY":
        narrative_context["narrative_type"] = "comparative"
    elif intent == "ONTOLOGY_QUERY":
        narrative_context["narrative_type"] = "ontology"
    elif intent == "GREETING_QUERY":
        narrative_context["narrative_type"] = "institutional"
    else:
        narrative_context["narrative_type"] = "unknown"

    # =====================================================
    # 2.5 Foco semántico institucional (SOLO GREETING_QUERY)
    # =====================================================
    if intent == "GREETING_QUERY":
        narrative_context["semantic_focus"].extend([
            "system_overview",
            "capabilities",
            "supported_query_types",
        ])

        narrative_context["notes_for_llm"].extend([
            "Introduce the K9 Mining Safety system.",
            "Explain what types of questions the system can handle.",
        ])



    # =====================================================
    # 3. Capas semánticas para el LLM
    # =====================================================
    narrative_context["narrative_intent"] = _infer_narrative_intent(
        intent=intent,
        operation=operation,
    )

    narrative_context["conceptual_axes"] = _infer_conceptual_axes(
        intent=intent,
        entity=entity,
    )

    narrative_context["narrative_constraints"] = _default_narrative_constraints()

    # =====================================================
    # 4. Consumir resultados OPERACIONALES (si existen)
    # =====================================================
    analysis = state.analysis or {}
    op = analysis.get("operational_analysis", {})
    


    if op:
        narrative_context["semantic_focus"].append("operational_evidence")

        narrative_context["key_entities"].extend(op.get("entities", []))
        narrative_context["key_risks"].extend(op.get("risks", []))
        narrative_context["signals"].extend(op.get("signals", []))

        if op.get("time_window"):
            narrative_context["temporal_markers"].append(
                op.get("time_window")
            )

    # =====================================================
    # 5. Consumir resultados ANALÍTICOS (si existen)
    # =====================================================
    an = analysis

    analysis_mode = analysis.get("analysis_mode")

    if an:
        if analysis_mode == "evidence_based":
            narrative_context["semantic_focus"].append("analytical_results")
        elif analysis_mode == "structural":
            narrative_context["semantic_focus"].append("structural_analysis")

        if "risk_summary" in an:
            rs = an.get("risk_summary", {})
            if rs.get("dominant_risk"):
                narrative_context["key_risks"].append(rs["dominant_risk"])

        if "risk_trajectories" in an:
            narrative_context["temporal_markers"].append("risk_trends")

        if "proactive_comparison" in an:
            narrative_context["comparisons"].append("proactive_vs_k9")


    # =====================================================
    # 6. Consumir resultados ONTOLÓGICOS (si existen)
    # =====================================================
    ont = analysis.get("ontology", {})

    if ont:
        narrative_context["semantic_focus"].append("ontology_context")
        narrative_context["key_entities"].extend(
            ont.get("entities", [])
        )

        narrative_context["notes_for_llm"].append(
            "Ontology concepts referenced; definitions exist in ontology layer."
        )

    # =====================================================
    # 7. Notas explícitas para el LLM
    # =====================================================
    narrative_context["notes_for_llm"].extend([
        "Use K9 cognitive framing; do not use generic safety explanations.",
        "Structure the explanation using conceptual_axes.",
        "Base the explanation strictly on provided evidence.",
    ])

    if is_composite:
        narrative_context["notes_for_llm"].append(
            "This is a composite request; ensure all sub-questions are addressed."
        )

    # =====================================================
    # 8. Persistencia y trazabilidad
    # =====================================================
    state.narrative_context = narrative_context

    state.reasoning.append(
        f"NarrativeNode: narrative context built "
        f"(type={narrative_context['narrative_type']}, "
        f"intent={narrative_context['narrative_intent']})."
    )

    return state
