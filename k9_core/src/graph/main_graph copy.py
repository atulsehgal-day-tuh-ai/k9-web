from langgraph.graph import StateGraph, START, END

from src.state.state import K9State

# --------------------------------------------------------------------------------------------------
# NODOS BASE DEL PIPELINE
# --------------------------------------------------------------------------------------------------
from src.nodes.intent_classifier import intent_classifier
from src.nodes.domain_guardrail import domain_guardrail
from src.nodes.load_context import load_context
from src.nodes.data_engine_node import data_engine_node
from src.nodes.occ_enrichment_node import occ_enrichment_node
from src.nodes.analyst_node import analyst_node
from src.nodes.router import router_node
from src.nodes.narrative_node import narrative_node
from src.nodes.metrics_node import metrics_node

# --------------------------------------------------------------------------------------------------
# NODOS FUNCIONALES / COGNITIVOS
# --------------------------------------------------------------------------------------------------
from src.nodes.llm_node import llm_node
from src.nodes.semantic_retrieval_node import semantic_retrieval_node
from src.nodes.proactive_model_node import proactive_model_node
from src.nodes.bowtie_node import bowtie_node
from src.nodes.fallback_node import fallback_node

# --------------------------------------------------------------------------------------------------
# NUEVO: NODO ONTOLÓGICO
# --------------------------------------------------------------------------------------------------
from src.nodes.ontology_query_node import OntologyQueryNode


# ==============================================================================================
# ROUTER CANÓNICO TEMPRANO (PRE-DATA ENGINE)
# ==============================================================================================
def route_pre_data_engine(state: K9State):
    """
    Router determinista temprano.
    Decide si el flujo es ontológico o factual.
    """
    command = getattr(state, "k9_command", None)

    if command and command.get("intent") == "ONTOLOGY_QUERY":
        state.reasoning.append(
            "PreRouter: ONTOLOGY_QUERY → OntologyQueryNode"
        )
        return "ontology"

    state.reasoning.append(
        "PreRouter: non-ontology intent → DataEngine pipeline"
    )
    return "factual"


def build_k9_graph():
    graph = StateGraph(K9State)

    # ==============================================================================================
    # REGISTRO DE NODOS
    # ==============================================================================================
    graph.add_node("intent", intent_classifier)
    graph.add_node("guardrail", domain_guardrail)
    graph.add_node("context", load_context)

    # Pipeline cognitivo determinista
    graph.add_node("data_engine", data_engine_node)
    graph.add_node("occ_enrichment", occ_enrichment_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("metrics", metrics_node)

    # Gobernanza
    graph.add_node("router", router_node)

    # Ramas funcionales
    graph.add_node("llm", llm_node)
    graph.add_node("semantic_retrieval", semantic_retrieval_node)
    graph.add_node("proactive_model", proactive_model_node)
    graph.add_node("bowtie", bowtie_node)
    graph.add_node("fallback", fallback_node)

    # NUEVO nodo ontológico
    ontology_query_node = OntologyQueryNode(
        ontology_path="data/ontology"
    )
    graph.add_node("ontology_query", ontology_query_node)

    # Salida única
    graph.add_node("narrative", narrative_node)

    # ==============================================================================================
    # FLUJO PRINCIPAL
    # ==============================================================================================
    graph.add_edge(START, "intent")
    graph.add_edge("intent", "guardrail")
    graph.add_edge("guardrail", "context")

    # ==============================================================================================
    # ROUTER CANÓNICO TEMPRANO (ANTES DEL DATA ENGINE)
    # ==============================================================================================
    graph.add_conditional_edges(
        "context",
        route_pre_data_engine,
        {
            "ontology": "ontology_query",
            "factual": "data_engine",
        },
    )

    # ==============================================================================================
    # PIPELINE FACTUAL EXISTENTE (SIN CAMBIOS)
    # ==============================================================================================
    graph.add_edge("data_engine", "occ_enrichment")
    graph.add_edge("occ_enrichment", "analyst")
    graph.add_edge("analyst", "metrics")
    graph.add_edge("metrics", "router")

    # ==============================================================================================
    # ROUTER DE INTENCIÓN EXISTENTE (GOBERNANZA, NO COGNICIÓN)
    # ==============================================================================================
    def route_intent(state: K9State):
        intent = state.intent

        valid_intents = {
            "greeting",
            "proactive_model",
            "proactive_model_contrafactual",
            "mining_general",
            "general_question",
            "bowtie",
            "riesgos",
        }

        if intent not in valid_intents:
            state.reasoning.append(
                f"RouterNode: intent '{intent}' no reconocido → fallback."
            )
            return "fallback"

        # ------------------------------------------------------------------
        # Ajuste semántico FASE 1
        # ------------------------------------------------------------------
        if intent == "riesgos":
            state.reasoning.append(
                "RouterNode FASE 1: intent 'riesgos' tratado como 'mining_general'."
            )
            return "mining_general"

        if intent == "proactive_model":
            state.reasoning.append(
                "RouterNode FASE 2 temprana: intent 'proactive_model' → "
                "se activa explicación proactivo vs K9."
            )
            return "proactive_model"

        state.reasoning.append(
            f"RouterNode: routing intent '{intent}'."
        )
        return intent

    graph.add_conditional_edges(
        "router",
        route_intent,
        {
            "greeting": "llm",
            "proactive_model": "proactive_model",
            "proactive_model_contrafactual": "proactive_model",
            "mining_general": "semantic_retrieval",
            "general_question": "semantic_retrieval",
            "bowtie": "bowtie",
            "fallback": "fallback",
        },
    )

    # ==============================================================================================
    # SALIDAS → NARRATIVE → END
    # ==============================================================================================
    graph.add_edge("ontology_query", "narrative")

    graph.add_edge("llm", "narrative")
    graph.add_edge("semantic_retrieval", "narrative")
    graph.add_edge("proactive_model", "narrative")
    graph.add_edge("bowtie", "narrative")
    graph.add_edge("fallback", "narrative")

    graph.add_edge("narrative", END)

    return graph.compile()
