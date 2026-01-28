from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

from src.graph.main_graph import build_k9_graph
from src.llm.factory import create_llm_client
from src.llm.language_bundle import load_k9_language_bundle
from src.llm.payload import (
    LLMPayload,
    LLMSystemContract,
    LLMUserContext,
    LLMK9Context,
    LLMKnowledgeScaffold,
)
from src.llm.validators import validate_llm_output_schema
from src.llm.json_utils import extract_json_object, safe_json_loads
from src.state.state import K9State

from app.config import APISettings
from app.data_catalog import collect_sources, describe_sources
from app.neo4j_client import Neo4jClient, Neo4jConfig


@dataclass(frozen=True)
class InterpretationResult:
    ok: bool
    parsed: Optional[Dict[str, Any]]
    error: Optional[str] = None


class K9Service:
    """
    K9Service: Hybrid runtime
    - Interpretation: NL -> K9 command via Gemini
    - Deterministic cognition: LangGraph on K9State
    - Synthesis: K9 -> Spanish answer via Gemini
    """

    def __init__(self):
        bundle = load_k9_language_bundle()
        self.knowledge = LLMKnowledgeScaffold(
            canonical_schema=bundle["schema"],
            domain_semantics=bundle["domain_semantics_es"],
            canonical_language=bundle["language"],
            examples_basic=bundle["examples_basic"],
            examples_advanced=bundle["examples_advanced"],
            meta_reasoning_examples=bundle["meta_reasoning_examples"],
        )

        # LLM client (Gemini) created from env (K9_PROVIDER, K9_GEMINI_API_KEY, K9_GEMINI_MODEL)
        self.llm = create_llm_client()

        # Compile graph once
        self.graph = build_k9_graph()

        # Optional: Neo4j client (knowledge graph)
        settings = APISettings()
        self._neo4j: Optional[Neo4jClient] = None
        if settings.neo4j_enabled:
            self._neo4j = Neo4jClient(
                Neo4jConfig(
                    uri=settings.neo4j_uri,
                    username=settings.neo4j_username,
                    password=settings.neo4j_password,
                    database=settings.neo4j_database,
                )
            )

    # ------------------------------------------------------------
    # 1) Interpretation (NL -> K9 command)
    # ------------------------------------------------------------
    def interpret(self, user_query: str, *, session_id: str = "api") -> InterpretationResult:
        payload = LLMPayload(
            system=LLMSystemContract(),
            session_id=session_id,
            active_phase="interpretation",
            is_composite=False,
            user=LLMUserContext(
                original_question=user_query,
                language="es",
                turn_index=0,
            ),
            k9=LLMK9Context(
                k9_command={},
                narrative_context=None,
                operational_analysis=None,
                analyst_results=None,
            ),
            knowledge=self.knowledge,
            instruction="Translate NL to K9 command",
        )

        raw = self.llm.generate(payload)
        json_str = extract_json_object(raw) or raw
        parsed, err = safe_json_loads(json_str)
        if parsed is None:
            return InterpretationResult(ok=False, parsed=None, error=f"Invalid JSON from LLM: {err}")

        ok, msg = validate_llm_output_schema(parsed)
        if not ok:
            return InterpretationResult(ok=False, parsed=parsed, error=f"Invalid K9 schema: {msg}")

        return InterpretationResult(ok=True, parsed=parsed)

    # ------------------------------------------------------------
    # 2) Deterministic cognition (graph invoke)
    # ------------------------------------------------------------
    def run_graph(
        self,
        *,
        user_query: str,
        k9_command: Dict[str, Any],
        active_event: Optional[Dict[str, Any]] = None,
        demo_mode: bool = False,
    ) -> K9State:
        # state.k9_command is the graph source of truth
        state = K9State(
            user_query=user_query,
            k9_command=k9_command,
            # keep a backward-compatible mirror for some legacy nodes
            context_bundle={"k9_command": k9_command},
            demo_mode=demo_mode,
            active_event=active_event,
        )

        result = self.graph.invoke(state)
        return result if isinstance(result, K9State) else K9State(**result)

    def build_trace(self, *, state: K9State, k9_command: Dict[str, Any]) -> Dict[str, Any]:
        analysis = state.analysis if isinstance(state.analysis, dict) else {}
        sources = collect_sources(analysis)
        return {
            "intent": (k9_command or {}).get("intent"),
            "entity": (k9_command or {}).get("entity"),
            "operation": (k9_command or {}).get("operation"),
            "time_context": state.time_context.model_dump() if state.time_context is not None else None,
            "data_slice": repr(state.data_slice) if state.data_slice is not None else None,
            "sources": describe_sources(sources),
            "nodes": state.reasoning,
        }

    def get_recommendations(self, *, risk_id: str) -> Optional[Dict[str, Any]]:
        """
        Prescriptive recommendations from the knowledge graph.
        Returns None if Neo4j is not configured.
        """
        if self._neo4j is None:
            return None

        # Controls (by property; ingester preserves riesgo_asociado on control nodes)
        crit = self._neo4j.query(
            "MATCH (c:ControlCritico {riesgo_asociado:$rid}) RETURN c.id AS id, c.nombre AS nombre, c.descripcion AS descripcion",
            {"rid": risk_id},
            limit=25,
        )
        prev = self._neo4j.query(
            "MATCH (c:ControlPreventivo {riesgo_asociado:$rid}) RETURN c.id AS id, c.nombre AS nombre, c.descripcion AS descripcion",
            {"rid": risk_id},
            limit=25,
        )
        barriers = self._neo4j.query(
            "MATCH (b:BarreraRecuperacion {riesgo_asociado:$rid}) RETURN b.id AS id, b.nombre AS nombre, b.descripcion AS descripcion",
            {"rid": risk_id},
            limit=25,
        )

        # Factors/exposure (from list on risk node)
        factors_exp = self._neo4j.query(
            """
MATCH (r:Riesgo {id:$rid})
UNWIND coalesce(r.factores_exposicion_relacionados, []) AS feId
MATCH (fe:FactorExposicion {id: feId})
RETURN fe.id AS id, fe.nombre AS nombre, fe.descripcion AS descripcion
""",
            {"rid": risk_id},
            limit=50,
        )

        causes = self._neo4j.query(
            """
MATCH (c:Causa {riesgo_asociado:$rid})
RETURN c.id AS id, c.nombre AS nombre, c.descripcion AS descripcion
""",
            {"rid": risk_id},
            limit=25,
        )

        return {
            "risk_id": risk_id,
            "critical_controls": crit,
            "preventive_controls": prev,
            "recovery_barriers": barriers,
            "exposure_factors": factors_exp,
            "causes": causes,
        }

    # ------------------------------------------------------------
    # 3) Synthesis (K9 -> Spanish answer)
    # ------------------------------------------------------------
    def synthesize(self, *, user_query: str, k9_command: Dict[str, Any], state: K9State, session_id: str = "api") -> Tuple[str, Dict[str, Any]]:
        synthesis_payload = LLMPayload(
            system=LLMSystemContract(),
            session_id=session_id,
            active_phase="synthesis",
            is_composite=False,
            user=LLMUserContext(
                original_question=user_query,
                language="es",
                turn_index=0,
            ),
            k9=LLMK9Context(
                k9_command=k9_command,
                narrative_context=state.narrative_context,
                operational_analysis=state.analysis,
                analyst_results=state.analysis,
            ),
            knowledge=self.knowledge,
            instruction="Translate K9 narrative to Spanish",
        )

        raw = self.llm.generate(synthesis_payload)
        json_str = extract_json_object(raw) or raw
        parsed, err = safe_json_loads(json_str)
        if not isinstance(parsed, dict) or parsed.get("type") != "FINAL_ANSWER":
            # Fail-soft: return raw text
            return raw.strip(), {"raw": raw, "parse_error": err}

        answer = parsed.get("answer")
        if not isinstance(answer, str):
            answer = json.dumps(answer, ensure_ascii=False, indent=2)

        return answer, parsed

