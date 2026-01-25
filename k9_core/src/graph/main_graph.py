from langgraph.graph import StateGraph, START, END

from src.state.state import K9State

# --------------------------------------------------------------------------------------------------
# NODOS BASE DEL PIPELINE
# --------------------------------------------------------------------------------------------------
from src.nodes.domain_guardrail import domain_guardrail
from src.nodes.load_context import load_context
from src.nodes.data_engine_node import data_engine_node
from src.nodes.occ_enrichment_node import occ_enrichment_node
from src.nodes.analyst_node import analyst_node
from src.nodes.metrics_node import metrics_node
from src.nodes.router import router_node
from src.nodes.narrative_node import narrative_node

# --------------------------------------------------------------------------------------------------
# NODOS FUNCIONALES
# --------------------------------------------------------------------------------------------------
from src.nodes.semantic_retrieval_node import semantic_retrieval_node
from src.nodes.proactive_model_node import proactive_model_node
from src.nodes.bowtie_node import bowtie_node
from src.nodes.fallback_node import fallback_node

# --------------------------------------------------------------------------------------------------
# NODO ONTOLÓGICO
# --------------------------------------------------------------------------------------------------
from src.nodes.ontology_query_node import OntologyQueryNode


# ==============================================================================================
# ROUTER TEMPRANO — ONTOLOGÍA vs FACTUAL
# ==============================================================================================
def route_pre_data_engine(state: K9State):
    cmd = state.k9_command or {}
    intent = cmd.get("intent")

    if intent == "ONTOLOGY_QUERY":
        state.reasoning.append(
            "PreRouter: ONTOLOGY_QUERY → ontology_query"
        )
        return "ontology"

    state.reasoning.append(
        f"PreRouter: intent={intent} → data_engine"
    )
    return "factual"


# ==============================================================================================
# ROUTER POST-ANÁLISIS — GOBERNANZA CANÓNICA
# ==============================================================================================
def route_post_analysis(state: K9State):
    cmd = state.k9_command or {}
    intent = cmd.get("intent")

    if intent in {
        "OPERATIONAL_QUERY",
        "ANALYTICAL_QUERY",
        "TEMPORAL_RELATION_QUERY",
        "COMPARATIVE_QUERY",
        "SYSTEM_QUERY",
    }:
        return "semantic_retrieval"

    if intent == "PROACTIVE_MODEL_QUERY":
        return "proactive_model"

    if intent == "BOWTIE_QUERY":
        return "bowtie"

    return "fallback"


# ==============================================================================================
# BUILD GRAPH
# ==============================================================================================
def build_k9_graph():
    graph = StateGraph(K9State)

    # ----------------------------------
    # Registro de nodos
    # ----------------------------------
    graph.add_node("guardrail", domain_guardrail)
    graph.add_node("context", load_context)

    graph.add_node("data_engine", data_engine_node)
    graph.add_node("occ_enrichment", occ_enrichment_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("metrics", metrics_node)

    graph.add_node("router", router_node)

    graph.add_node("semantic_retrieval", semantic_retrieval_node)
    graph.add_node("proactive_model", proactive_model_node)
    graph.add_node("bowtie", bowtie_node)
    graph.add_node("fallback", fallback_node)

    ontology_query_node = OntologyQueryNode(
        ontology_path="data/ontology"
    )
    graph.add_node("ontology_query", ontology_query_node)

    graph.add_node("narrative", narrative_node)

    # ----------------------------------
    # Flujo principal
    # ----------------------------------
    graph.add_edge(START, "guardrail")
    graph.add_edge("guardrail", "context")

    graph.add_conditional_edges(
        "context",
        route_pre_data_engine,
        {
            "ontology": "ontology_query",
            "factual": "data_engine",
        },
    )

    graph.add_edge("data_engine", "occ_enrichment")
    graph.add_edge("occ_enrichment", "analyst")
    graph.add_edge("analyst", "metrics")
    graph.add_edge("metrics", "router")

    graph.add_conditional_edges(
        "router",
        route_post_analysis,
        {
            "semantic_retrieval": "semantic_retrieval",
            "proactive_model": "proactive_model",
            "bowtie": "bowtie",
            "fallback": "fallback",
        },
    )

    graph.add_edge("ontology_query", "narrative")
    graph.add_edge("semantic_retrieval", "narrative")
    graph.add_edge("proactive_model", "narrative")
    graph.add_edge("bowtie", "narrative")
    graph.add_edge("fallback", "narrative")

    graph.add_edge("narrative", END)

    return graph.compile()
