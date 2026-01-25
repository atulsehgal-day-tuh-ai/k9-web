# src/llm/prompts.py
from __future__ import annotations

import json
from typing import Dict, Any


def build_prompt_human_to_k9(user_query: str, bundle: Dict[str, Any]) -> str:
    """
    STRICT NL → K9 translation prompt.

    Activates CANONICAL STRUCTURAL REASONING:
    Intent → Operation → Entity → Payload

    - NO free reasoning
    - NO narrative
    - NO execution
    - ONLY canonical decision mapping
    """

    rules = [
        # ==================================================
        # ROLE
        # ==================================================
        "You are the canonical linguistic interface of the K9 Mining Safety system.",
        "Your task is to translate Spanish user queries into STRICT canonical K9 JSON commands.",
        "You do NOT execute logic or access data.",
        "You MUST perform STRUCTURAL CANONICAL REASONING before producing JSON.",

        # ==================================================
        # CANONICAL REASONING CONTRACT (CRITICAL)
        # ==================================================
        "Before generating the JSON, you MUST internally determine:",
        "  1) The canonical intent",
        "  2) The REQUIRED canonical operation for that intent",
        "  3) The required entity scope",
        "  4) The complete schema-valid payload",
        "If any required operation is missing, the output is INVALID.",

        # ==================================================
        # OUTPUT FORMAT — ABSOLUTE
        # ==================================================
        "You MUST return exactly ONE valid JSON object and NOTHING ELSE.",
        "The JSON MUST contain a top-level field named 'type'.",
        "Valid values for 'type' are:",
        "  - 'K9_COMMAND'",
        "  - 'COMPOSITE_K9_COMMAND'",
        "  - 'CLARIFICATION_REQUEST'",

        # ==================================================
        # K9_COMMAND STRUCTURE (CRITICAL)
        # ==================================================
        "If type == 'K9_COMMAND', the JSON MUST contain:",
        "  - TOP-LEVEL field: 'intent'",
        "  - TOP-LEVEL field: 'payload'",
        "AND the payload MUST ALSO contain:",
        "  - field 'intent' with the SAME value as the top-level intent.",
        "  - field 'operation' IF REQUIRED by the canonical schema.",
        "This duplication is MANDATORY.",

        # ==================================================
        # OPERATION SELECTION RULE (NEW — KEY FIX)
        # ==================================================
        "If the intent involves:",
        "  - comparison, ranking, selection of highest/lowest → operation MUST be 'rank'",
        "  - explanation, causality, drivers, factors → operation MUST be 'explain'",
        "  - evolution, trends, trajectories → operation MUST be 'trend'",
        "  - counting or distribution → operation MUST be 'aggregate'",
        "NEVER omit 'operation' when the schema defines it.",

        # ==================================================
        # REQUIRED ENTITY RULE (GLOBAL RISKS)
        # ==================================================
        "If the canonical schema requires payload.entity:",
        "  - AND the query is GLOBAL or COMPARATIVE",
        "  - AND no specific risk ID is mentioned",
        "THEN payload.entity MUST be 'ALL_RISKS'.",
        "This is a K9 linguistic rule. DO NOT request clarification.",

        # ==================================================
        # PROACTIVE MODEL — STRICT RULE
        # ==================================================
        "If the proactive model is mentioned:",
        "  - Use it ONLY as comparative evidence.",
        "  - NEVER derive causality or operations from it.",

        # ==================================================
        # COMPOSITE_K9_COMMAND
        # ==================================================
        "If the query contains more than one action:",
        "  - You MUST use COMPOSITE_K9_COMMAND.",
        "  - EACH step MUST be a FULL K9_COMMAND.",
        "  - Entities produced by one step MAY be referenced by the next.",

        # ==================================================
        # CLARIFICATION
        # ==================================================
        "Return CLARIFICATION_REQUEST ONLY IF a REQUIRED field cannot be populated",
        "AND no canonical rule applies.",
        "Do NOT ask for clarification when time windows are explicit.",

        # ==================================================
        # HARD FAIL CONDITIONS
        # ==================================================
        "NEVER invent operations, entities, metrics, or schema fields.",
        "NEVER omit 'operation' when required.",
        "NEVER return partial JSON.",
    ]

    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

====================
K9 CANONICAL SCHEMA
====================
{json.dumps(bundle.get("schema", {}), ensure_ascii=False, indent=2)}

====================
K9 LANGUAGE
====================
{json.dumps(bundle.get("language", {}), ensure_ascii=False, indent=2)}

====================
K9 DOMAIN SEMANTICS
====================
{json.dumps(bundle.get("domain_semantics_es", {}), ensure_ascii=False, indent=2)}

====================
META-REASONING EXAMPLES (AUTHORITATIVE)
====================
{json.dumps(bundle.get("meta_reasoning_examples", []), ensure_ascii=False, indent=2)}

====================
ADVANCED EXAMPLES
====================
{json.dumps(bundle.get("examples_advanced", []), ensure_ascii=False, indent=2)}

====================
BASIC EXAMPLES
====================
{json.dumps(bundle.get("examples_basic", []), ensure_ascii=False, indent=2)}

====================
USER QUERY (SPANISH)
====================
{user_query}
""".strip()

    return prompt


# ======================================================
# K9 → HUMANO (SYNTHESIS)
# ======================================================
def build_prompt_k9_to_human(narrative: str) -> str:
    """
    Deterministic K9 narrative → Spanish answer.
    NO inference, NO reasoning, NO enrichment.
    """

    rules = [
        "You translate K9 narrative into clear, professional Spanish.",
        "You MUST NOT add facts, interpretations, or recommendations.",
        "You MUST preserve the exact meaning and structure.",
        "Return ONLY a JSON object with:",
        "  - type = 'FINAL_ANSWER'",
        "  - answer = '<Spanish text>'",
    ]

    prompt = f"""
SYSTEM RULES:
- {' '.join(rules)}

K9 NARRATIVE (INPUT):
{narrative}
""".strip()

    return prompt
