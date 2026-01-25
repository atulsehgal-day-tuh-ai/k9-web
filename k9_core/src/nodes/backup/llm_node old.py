# src/nodes/llm_node.py

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple, List

from google import genai

from src.state.state import K9State
from config.settings import get_gemini_api_key


# ----------------------------
# Defaults (Demo-scope)
# ----------------------------

DEFAULT_INTENTS = [
    "GREETING_QUERY",
    "ONTOLOGY_QUERY",
    "OPERATIONAL_QUERY",
    "ANALYTICAL_QUERY",
    "COMPARATIVE_QUERY",
    "TEMPORAL_RELATION_QUERY",
    "SYSTEM_QUERY",
]

DEFAULT_ENTITIES = [
    # factual
    "observations",
    "events",
    "audits",
    "fdo",
    "trajectories",
    "signals",
    "proactive_model",
    "data_coverage",
    # ontology
    "risk",
    "task",
    "role",
    "control",
    "cause",
    "consequence",
    "bowtie",
    "area",
    "ppe",
]

DEFAULT_OPERATIONS = [
    # general / factual
    "list",
    "count",
    "summarize",
    "retrieve_by_id",
    # analytical / temporal / comparative
    "evolution",
    "sequence",
    "window",
    "rank",
    "detect_absence",
    "compare",
    # ontology (v1.2 official subset)
    "retrieve",
    "describe",
    "get_controls",
    "get_causes",
    "get_consequences",
    "get_bowtie",
    "get_tasks_and_roles",
]

DEFAULT_TIME_VALUES = [
    "last_week",
    "last_2_weeks",
    "last_4_weeks",
    "last_month",
    "week_01_2025",
    "pre_post",
]


# ----------------------------
# Helpers
# ----------------------------

def _ensure_context_bundle(state: K9State) -> Dict[str, Any]:
    if state.context_bundle is None:
        state.context_bundle = {}
    return state.context_bundle


def _strip_code_fences(text: str) -> str:
    # Removes ```json ... ``` fences if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> Optional[str]:
    """
    Try to extract the first valid JSON object substring.
    """
    text = _strip_code_fences(text)
    # Fast path: already JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Attempt to find the first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


def _safe_json_loads(raw: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        return json.loads(raw), None
    except Exception as e:
        return None, str(e)


def _validate_llm_output_schema(obj: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Minimal contract validation:
    - type must be K9_COMMAND or CLARIFICATION_REQUEST
    - For K9_COMMAND: payload must contain intent/entity/operation/output at least
    - For CLARIFICATION_REQUEST: must contain reason and options (<=3)
    """
    if "type" not in obj:
        return False, "Missing field: type"

    out_type = obj["type"]
    if out_type not in ("K9_COMMAND", "CLARIFICATION_REQUEST"):
        return False, f"Invalid type: {out_type}"

    if out_type == "K9_COMMAND":
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            return False, "K9_COMMAND requires payload object"

        for k in ("intent", "entity", "operation", "output"):
            if k not in payload:
                return False, f"K9_COMMAND.payload missing field: {k}"

        if not isinstance(payload.get("filters", {}), dict):
            return False, "K9_COMMAND.payload.filters must be an object"
        if payload.get("time") is not None and not isinstance(payload.get("time"), dict):
            return False, "K9_COMMAND.payload.time must be an object if provided"

        return True, "OK"

    # CLARIFICATION_REQUEST
    reason = obj.get("reason")
    options = obj.get("options")
    if not reason:
        return False, "CLARIFICATION_REQUEST missing field: reason"
    if not isinstance(options, list) or len(options) == 0:
        return False, "CLARIFICATION_REQUEST requires non-empty options list"
    if len(options) > 3:
        return False, "CLARIFICATION_REQUEST options must be <= 3"

    return True, "OK"


def _build_prompt_human_to_k9(
    user_query: str,
    intents: List[str],
    entities: List[str],
    operations: List[str],
    time_values: List[str],
    demo_rules: Dict[str, Any],
) -> str:
    """
    Strict JSON-only output prompt.
    """
    rules = [
        "You are a translation layer for the K9 system. You do NOT execute queries.",
        "Return ONLY a single JSON object. No prose. No markdown.",
        "If the user request cannot be mapped to ONE unique K9 command, return CLARIFICATION_REQUEST.",
        "Never guess a vague time range (e.g., 'recently', 'lately'). Ask for clarification.",
        "Never invent domain facts or causes. Never recommend operational actions.",
        "Options for clarification must be <= 3 and must be clearly distinct.",
    ]

    # Allow demo overrides (minimal)
    if demo_rules.get("max_clarification_options"):
        rules.append(f"Clarification options maximum: {demo_rules['max_clarification_options']}")

    schema_hint = {
        "K9_COMMAND": {
            "type": "K9_COMMAND",
            "payload": {
                "intent": "<one_of_intents>",
                "entity": "<one_of_entities>",
                "operation": "<one_of_operations>",
                "filters": {},
                "time": {"type": "absolute|relative|window", "value": "<time_value>"},
                "output": "raw|analysis|narrative"
            }
        },
        "CLARIFICATION_REQUEST": {
            "type": "CLARIFICATION_REQUEST",
            "reason": "AMBIGUOUS_INTENT|AMBIGUOUS_OPERATION|AMBIGUOUS_TIME|AMBIGUOUS_ENTITY|OUT_OF_DOMAIN",
            "options": [
                {"label": "<short>", "description": "<what you need from the user>"},
            ]
        }
    }

    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

ALLOWED INTENTS:
{intents}

ALLOWED ENTITIES:
{entities}

ALLOWED OPERATIONS:
{operations}

ALLOWED RELATIVE/WINDOW TIME VALUES (examples):
{time_values}

OUTPUT SCHEMA EXAMPLES (do not copy literally; produce valid JSON):
{json.dumps(schema_hint, ensure_ascii=False, indent=2)}

USER QUERY:
{user_query}
""".strip()

    return prompt


def _build_prompt_k9_to_human(narrative: str) -> str:
    rules = [
        "You translate K9 narrative to clear professional Spanish.",
        "Do NOT add new facts, do NOT infer causes, do NOT recommend actions.",
        "Keep it concise, technical, and faithful.",
        "Return ONLY a single JSON object with fields: type='FINAL_ANSWER' and answer='<text>'.",
    ]
    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

K9 NARRATIVE (input):
{narrative}
""".strip()
    return prompt


# ----------------------------
# Main Node
# ----------------------------

def llm_node(state: K9State) -> K9State:
    """
    LLM Node (Contract-based)
    - Mode A (default): HUMAN_TO_K9 -> outputs K9_COMMAND or CLARIFICATION_REQUEST (structured)
    - Mode B: K9_TO_HUMAN -> outputs FINAL_ANSWER (structured) using provided narrative
    """
    ctx = _ensure_context_bundle(state)

    # Mode selection (explicit if provided)
    mode = (ctx.get("llm_mode") or "HUMAN_TO_K9").upper()

    # Load allowed vocab (prefer context_bundle overrides)
    intents = ctx.get("allowed_intents") or DEFAULT_INTENTS
    entities = ctx.get("allowed_entities") or DEFAULT_ENTITIES
    operations = ctx.get("allowed_operations") or DEFAULT_OPERATIONS
    time_values = ctx.get("allowed_time_values") or DEFAULT_TIME_VALUES

    demo_rules = ctx.get("demo_rules") or {"max_clarification_options": 3}

    api_key = get_gemini_api_key()
    if not api_key:
        # No LLM available → deterministic fallback (clarification)
        state.reasoning.append("LLM Node: missing API key -> returning CLARIFICATION_REQUEST.")
        out = {
            "type": "CLARIFICATION_REQUEST",
            "reason": "OUT_OF_DOMAIN",
            "options": [
                {"label": "config", "description": "LLM no disponible (API key). Proporcione configuración o ejecute en modo canónico."}
            ],
        }
        ctx["llm_output"] = out
        state.answer = "LLM no disponible. Proporcione configuración (API key) o use comandos K9 canónicos."
        state.intent = "CLARIFICATION_REQUEST"
        return state

    client = genai.Client(api_key=api_key)

    try:
        if mode == "K9_TO_HUMAN":
            # Expect narrative in context_bundle or state.answer-like field (keep compatibility)
            narrative = ctx.get("narrative") or ctx.get("k9_narrative") or ""
            if not narrative:
                # If nothing to translate, ask for required input
                out = {
                    "type": "CLARIFICATION_REQUEST",
                    "reason": "AMBIGUOUS_OPERATION",
                    "options": [
                        {"label": "narrative", "description": "No hay narrativa K9 para traducir. Proporcione narrative en context_bundle."}
                    ],
                }
                ctx["llm_output"] = out
                state.answer = "Falta narrativa K9 para traducir."
                state.intent = "CLARIFICATION_REQUEST"
                state.reasoning.append("LLM Node: missing narrative for K9_TO_HUMAN.")
                return state

            prompt = _build_prompt_k9_to_human(narrative)
            response = client.models.generate_content(
                model=ctx.get("llm_model") or "models/gemini-2.5-flash",
                contents=prompt
            )
            raw_text = (response.text or "").strip()

            # Expect JSON {type: FINAL_ANSWER, answer: "..."}
            raw_json = _extract_json_object(raw_text)
            if not raw_json:
                # fallback: treat as answer text but still structured
                out = {"type": "FINAL_ANSWER", "answer": raw_text}
            else:
                parsed, err = _safe_json_loads(raw_json)
                if not parsed or "answer" not in parsed:
                    out = {"type": "FINAL_ANSWER", "answer": raw_text}
                else:
                    out = parsed

            ctx["llm_output"] = out
            state.answer = out.get("answer")  # user-facing
            state.intent = "FINAL_ANSWER"
            state.reasoning.append("LLM Node: K9_TO_HUMAN translation produced FINAL_ANSWER.")
            return state

        # -------------------------
        # Mode: HUMAN_TO_K9 (default)
        # -------------------------
        user_query = (state.user_query or "").strip()
        if not user_query:
            out = {
                "type": "CLARIFICATION_REQUEST",
                "reason": "AMBIGUOUS_OPERATION",
                "options": [
                    {"label": "query", "description": "No se recibió una consulta. Indique qué desea consultar."}
                ],
            }
            ctx["llm_output"] = out
            state.answer = "No recibí una consulta. Indique qué desea consultar."
            state.intent = "CLARIFICATION_REQUEST"
            state.reasoning.append("LLM Node: empty user_query -> CLARIFICATION_REQUEST.")
            return state

        prompt = _build_prompt_human_to_k9(
            user_query=user_query,
            intents=intents,
            entities=entities,
            operations=operations,
            time_values=time_values,
            demo_rules=demo_rules,
        )

        response = client.models.generate_content(
            model=ctx.get("llm_model") or "models/gemini-2.5-flash",
            contents=prompt
        )

        raw_text = (response.text or "").strip()
        raw_json = _extract_json_object(raw_text)
        if not raw_json:
            raise ValueError("LLM did not return a JSON object.")

        parsed, err = _safe_json_loads(raw_json)
        if not parsed:
            raise ValueError(f"Invalid JSON from LLM: {err}")

        ok, msg = _validate_llm_output_schema(parsed)
        if not ok:
            raise ValueError(f"LLM output schema invalid: {msg}")

        ctx["llm_output"] = parsed

        if parsed["type"] == "K9_COMMAND":
            payload = parsed["payload"]
            ctx["k9_command"] = payload

            # Compatibility with legacy nodes/tests that still read state.intent
            state.intent = payload.get("intent", "")

            # DO NOT set state.answer here (core will execute next)
            state.reasoning.append(
                f"LLM Node: produced K9_COMMAND intent={payload.get('intent')} entity={payload.get('entity')} op={payload.get('operation')}."
            )
            return state

        # Clarification request (user-facing)
        reason = parsed.get("reason", "AMBIGUOUS")
        options = parsed.get("options", [])
        lines = ["Necesito un poco más de precisión para continuar."]

        # Keep to <= 3 options (already validated)
        for i, opt in enumerate(options, start=1):
            label = (opt or {}).get("label", f"opcion_{i}")
            desc = (opt or {}).get("description", "")
            lines.append(f"{i}. {label}: {desc}".strip())

        state.answer = "\n".join(lines)
        state.intent = "CLARIFICATION_REQUEST"
        state.reasoning.append(f"LLM Node: CLARIFICATION_REQUEST reason={reason}.")
        return state

    except Exception as e:
        # Fail closed (do not invent)
        state.reasoning.append(f"LLM Node ERROR (fail-closed): {str(e)}")
        out = {
            "type": "CLARIFICATION_REQUEST",
            "reason": "AMBIGUOUS_OPERATION",
            "options": [
                {"label": "retry", "description": "No fue posible generar un comando canónico válido. Reformule o especifique intent/entidad/tiempo."}
            ],
        }
        ctx["llm_output"] = out
        state.answer = "No fue posible generar un comando canónico válido. Reformule o especifique intent/entidad/tiempo."
        state.intent = "CLARIFICATION_REQUEST"
        return state
