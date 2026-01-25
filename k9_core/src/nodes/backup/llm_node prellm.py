# src/nodes/llm_node.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from google import genai

from src.state.state import K9State
from config.settings import get_gemini_api_key


# ======================================================
# K9 Language Bundle Paths (OFICIAL)
# ======================================================
# We resolve relative to this file to avoid CWD issues in pytest.
LANGUAGE_DIR = Path(__file__).resolve().parents[1] / "language"

SCHEMA_PATH = LANGUAGE_DIR / "k9_canonical_schema_v1_2.json"
LANGUAGE_PATH = LANGUAGE_DIR / "k9_language_v1_1.json"
ONTOLOGY_OPS_PATH = LANGUAGE_DIR / "k9_ontology_operations_v1_2.json"
EXAMPLES_BASIC_PATH = LANGUAGE_DIR / "k9_examples_basic.json"
EXAMPLES_ADVANCED_PATH = LANGUAGE_DIR / "k9_examples_advanced.json"

# New: Spanish domain grounding (OCC/OPG/FDO/audit/event subtypes/IDs/areas/risk IDs)
DOMAIN_SEMANTICS_ES_PATH = LANGUAGE_DIR / "k9_domain_semantics_es.json"


# ======================================================
# Internal cache (avoid re-reading JSON every call)
# ======================================================
_BUNDLE_CACHE: Optional[Dict[str, Any]] = None


# ======================================================
# Loaders
# ======================================================
def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"K9 language file not found: {path.as_posix()}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_k9_language_bundle(force_reload: bool = False) -> Dict[str, Any]:
    """
    Loads the complete language bundle used by the LLM translator.
    This is NOT used by the deterministic core.
    """
    global _BUNDLE_CACHE
    if _BUNDLE_CACHE is not None and not force_reload:
        return _BUNDLE_CACHE

    bundle = {
        "schema": _load_json(SCHEMA_PATH),
        "language": _load_json(LANGUAGE_PATH),
        "ontology_ops": _load_json(ONTOLOGY_OPS_PATH),
        "examples_basic": _load_json(EXAMPLES_BASIC_PATH),
        "examples_advanced": _load_json(EXAMPLES_ADVANCED_PATH),
    }

    # Domain semantics is required for Spanish → English K9 mapping in demo.
    # If missing, fail closed with a clear error (do not silently degrade).
    bundle["domain_semantics_es"] = _load_json(DOMAIN_SEMANTICS_ES_PATH)

    _BUNDLE_CACHE = bundle
    return bundle


# ======================================================
# Helpers
# ======================================================
def _ensure_context_bundle(state: K9State) -> Dict[str, Any]:
    if state.context_bundle is None:
        state.context_bundle = {}
    return state.context_bundle


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> Optional[str]:
    """
    Extract the first JSON object substring from model output.
    """
    text = _strip_code_fences(text)
    if text.startswith("{") and text.endswith("}"):
        return text

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
    Contract validation (minimal, deterministic):
    - type must be K9_COMMAND or CLARIFICATION_REQUEST
    - K9_COMMAND.payload must contain intent/entity/operation/output
    - CLARIFICATION_REQUEST must contain reason + options (<=3)
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

        if "filters" in payload and not isinstance(payload.get("filters"), dict):
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

    # ensure option objects shape
    for i, opt in enumerate(options):
        if not isinstance(opt, dict):
            return False, f"CLARIFICATION_REQUEST.options[{i}] must be an object"
        if "label" not in opt or "description" not in opt:
            return False, f"CLARIFICATION_REQUEST.options[{i}] missing label/description"

    return True, "OK"

def _validate_composite_llm_output_schema(obj: Dict[str, Any]) -> Tuple[bool, str]:
    if obj.get("type") != "COMPOSITE_K9_COMMAND":
        return False, "Invalid composite type"

    plan = obj.get("plan")
    if not isinstance(plan, list) or len(plan) == 0:
        return False, "COMPOSITE_K9_COMMAND requires non-empty plan list"

    for i, step in enumerate(plan):
        if step.get("type") != "K9_COMMAND":
            return False, f"plan[{i}] must be type K9_COMMAND"

        payload = step.get("payload")
        if not isinstance(payload, dict):
            return False, f"plan[{i}].payload must be object"

        for k in ("intent", "entity", "operation", "output"):
            if k not in payload:
                return False, f"plan[{i}].payload missing field: {k}"

    return True, "OK"

# ======================================================
# Prompt builders
# ======================================================
def _build_prompt_human_to_k9(user_query: str, bundle: Dict[str, Any]) -> str:
    """
    Builds a STRICT translation prompt using:
    - canonical schema
    - canonical language (intents/entities/operations/time/output)
    - ontology ops (v1.2)
    - examples (basic + advanced)
    - domain semantics ES (OCC/OPG/FDO/audits/event types/IDs/areas/risk IDs)
    """

    # Explicit rules for ambiguity & ontology awareness:
    rules = [
        "You are the translation layer of the K9 Mining Safety system.",
        "You NEVER execute logic, queries, retrieval, or analysis.",
        "You translate the user request into ONE cognitive K9 command."
        "A cognitive command may be a single K9_COMMAND or a COMPOSITE_K9_COMMAND."        
        "Return ONLY one JSON object. No prose. No markdown.",
        "If the request cannot be mapped to ONE unique command, return CLARIFICATION_REQUEST.",
        "Never guess vague time (e.g., 'últimamente', 'estas semanas', 'recientemente'). Ask for clarification.",
        "Never invent IDs. If an ID is required and missing, ask for clarification.",
        "Never invent causality, recommendations, or operational actions.",
        "Do not mix ontology world with synthetic data world in a single command.",
        "IMPORTANT: There exists an ontology (YAML-backed) with definitions and relationships. "
        "If the user asks 'qué es', 'definición', 'controles', 'causas', 'consecuencias', 'bowtie', 'roles expuestos', "
        "translate to ONTOLOGY_QUERY using the official ontology operations. Do NOT answer from memory."
        "You MAY return a COMPOSITE_K9_COMMAND when a single user question logically requires multiple cognitive steps.",
        "A composite command represents a cognitive plan, not execution.",
        "Each step must be a valid K9_COMMAND with its own intent.",
        "Do NOT decompose into low-level instructions.",
        "Do NOT split unless the user intent is clearly composite.",

    ]

    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

====================
K9 CANONICAL SCHEMA (AUTHORITATIVE)
====================
{json.dumps(bundle["schema"], ensure_ascii=False, indent=2)}

====================
K9 LANGUAGE (INTENTS / ENTITIES / OPERATIONS / TIME / OUTPUT)
====================
{json.dumps(bundle["language"], ensure_ascii=False, indent=2)}

====================
K9 ONTOLOGY OPERATIONS (v1.2 OFFICIAL)
====================
{json.dumps(bundle["ontology_ops"], ensure_ascii=False, indent=2)}

====================
K9 DOMAIN SEMANTICS (SPANISH USER TERMS → K9 CONCEPTS)
- Includes: OCC/OPG, FDO, audit types, incident types, areas IDs, risk IDs, and ID-awareness rules.
====================
{json.dumps(bundle["domain_semantics_es"], ensure_ascii=False, indent=2)}

====================
EXAMPLES (BASIC)
====================
{json.dumps(bundle["examples_basic"], ensure_ascii=False, indent=2)}

====================
EXAMPLES (ADVANCED – SCREENING)
====================
{json.dumps(bundle["examples_advanced"], ensure_ascii=False, indent=2)}

====================
USER QUERY (SPANISH)
====================
{user_query}
""".strip()

    return prompt


def _build_prompt_k9_to_human(narrative: str) -> str:
    """
    K9 narrative → Spanish user-facing answer.
    The narrative is already produced by deterministic nodes (NarrativeNode).
    The LLM must not add facts.
    """
    rules = [
        "You translate K9 narrative to clear professional Spanish.",
        "Do NOT add new facts, do NOT infer causes, do NOT recommend actions.",
        "Keep it concise, technical, and faithful to input.",
        "Return ONLY a single JSON object with fields: type='FINAL_ANSWER' and answer='<text>'."
    ]

    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

K9 NARRATIVE (INPUT):
{narrative}
""".strip()

    return prompt


# ======================================================
# Main Node
# ======================================================
def llm_node(state: K9State) -> K9State:
    """
    LLM Node — K9 Translator (Contract-based)

    Modes:
    - HUMAN_TO_K9 (default): Spanish user query → K9 command (K9_COMMAND) or clarification (CLARIFICATION_REQUEST)
    - K9_TO_HUMAN: deterministic narrative → FINAL_ANSWER (Spanish)

    Notes:
    - This node is the *translator*, not a decider.
    - The deterministic core validates and executes.
    """

    ctx = _ensure_context_bundle(state)
    mode = (ctx.get("llm_mode") or "HUMAN_TO_K9").upper()

    api_key = get_gemini_api_key()
    if not api_key:
        # fail-closed: no LLM available
        state.reasoning.append("LLM Node: missing API key -> CLARIFICATION_REQUEST (fail-closed).")
        out = {
            "type": "CLARIFICATION_REQUEST",
            "reason": "OUT_OF_DOMAIN",
            "options": [
                {
                    "label": "config",
                    "description": "LLM no disponible (API key). Proporcione configuración o use comandos K9 canónicos."
                }
            ],
        }
        ctx["llm_output"] = out
        state.answer = "LLM no disponible. Proporcione configuración (API key) o use comandos K9 canónicos."
        state.intent = "CLARIFICATION_REQUEST"
        return state

    client = genai.Client(api_key=api_key)

    try:
        # --------------------------------------------------
        # Mode: K9_TO_HUMAN
        # --------------------------------------------------
        if mode == "K9_TO_HUMAN":
            narrative = ctx.get("narrative") or ctx.get("k9_narrative") or ""
            if not narrative:
                out = {
                    "type": "CLARIFICATION_REQUEST",
                    "reason": "AMBIGUOUS_OPERATION",
                    "options": [
                        {
                            "label": "narrative",
                            "description": "No hay narrativa K9 para traducir. Proporcione 'narrative' en context_bundle."
                        }
                    ],
                }
                ctx["llm_output"] = out
                state.answer = "Falta narrativa K9 para traducir."
                state.intent = "CLARIFICATION_REQUEST"
                state.reasoning.append("LLM Node: missing narrative in K9_TO_HUMAN -> CLARIFICATION_REQUEST.")
                return state

            prompt = _build_prompt_k9_to_human(narrative)
            response = client.models.generate_content(
                model=ctx.get("llm_model") or "models/gemini-2.5-flash",
                contents=prompt
            )

            raw_text = (response.text or "").strip()
            raw_json = _extract_json_object(raw_text)

            if raw_json:
                parsed, err = _safe_json_loads(raw_json)
                if parsed and isinstance(parsed, dict) and parsed.get("type") == "FINAL_ANSWER" and "answer" in parsed:
                    out = parsed
                else:
                    out = {"type": "FINAL_ANSWER", "answer": raw_text}
            else:
                out = {"type": "FINAL_ANSWER", "answer": raw_text}

            ctx["llm_output"] = out
            state.answer = out.get("answer", "")
            state.intent = "FINAL_ANSWER"
            state.reasoning.append("LLM Node: K9_TO_HUMAN -> FINAL_ANSWER.")
            return state

        # --------------------------------------------------
        # Mode: HUMAN_TO_K9 (default)
        # --------------------------------------------------
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

        # Load the complete bundle (schema + language + ontology ops + examples + semantics ES)
        bundle = _load_k9_language_bundle(force_reload=bool(ctx.get("force_reload_language_bundle")))

        prompt = _build_prompt_human_to_k9(user_query=user_query, bundle=bundle)

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

        if parsed["type"] == "K9_COMMAND":
            ok, msg = _validate_llm_output_schema(parsed)
            if not ok:
                raise ValueError(f"K9_COMMAND invalid: {msg}")

        elif parsed["type"] == "COMPOSITE_K9_COMMAND":
            ok, msg = _validate_composite_llm_output_schema(parsed)
            if not ok:
                raise ValueError(f"COMPOSITE_K9_COMMAND invalid: {msg}")

        elif parsed["type"] == "CLARIFICATION_REQUEST":
            ok, msg = _validate_llm_output_schema(parsed)
            if not ok:
                raise ValueError(f"CLARIFICATION_REQUEST invalid: {msg}")

        else:
            raise ValueError(f"Unknown LLM output type: {parsed.get('type')}")

        ctx["llm_output"] = parsed

        if parsed["type"] == "K9_COMMAND":
            payload = parsed["payload"]
            ctx["k9_command"] = payload

            # Compatibility: legacy nodes/tests may still read state.intent
            state.intent = payload.get("intent", "")

            # DO NOT set state.answer here; deterministic core executes next
            state.reasoning.append(
                f"LLM Node: produced K9_COMMAND intent={payload.get('intent')} entity={payload.get('entity')} op={payload.get('operation')}."
            )
            return state
        
        # --- NEW: Composite command handling ---
        if parsed["type"] == "COMPOSITE_K9_COMMAND":
            ok, msg = _validate_composite_llm_output_schema(parsed)
            if not ok:
                raise ValueError(f"Invalid COMPOSITE_K9_COMMAND: {msg}")

            ctx["k9_composite_plan"] = parsed["plan"]
            ctx["k9_composite_output"] = parsed.get("output")

            # Compatibility marker
            state.intent = "COMPOSITE_QUERY"

            state.reasoning.append(
                f"LLM Node: produced COMPOSITE_K9_COMMAND with {len(parsed['plan'])} steps."
            )
            return state


        # CLARIFICATION_REQUEST
        reason = parsed.get("reason", "AMBIGUOUS")
        options = parsed.get("options", [])
        lines = ["Necesito un poco más de precisión para continuar."]

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
                {
                    "label": "retry",
                    "description": "No fue posible generar un comando canónico válido. Reformule o especifique intent/entidad/tiempo/IDs."
                }
            ],
        }
        ctx["llm_output"] = out
        state.answer = "No fue posible generar un comando canónico válido. Reformule o especifique intent/entidad/tiempo/IDs."
        state.intent = "CLARIFICATION_REQUEST"
        return state
