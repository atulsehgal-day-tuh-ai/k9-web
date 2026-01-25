# src/llm/validators.py
from __future__ import annotations

from typing import Dict, Tuple


def validate_llm_output_schema(obj: Dict) -> Tuple[bool, str]:
    if "type" not in obj:
        return False, "Missing field: type"

    out_type = obj["type"]
    if out_type not in ("K9_COMMAND", "COMPOSITE_K9_COMMAND", "CLARIFICATION_REQUEST"):
        return False, f"Invalid type: {out_type}"

    if out_type == "K9_COMMAND":
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            return False, "K9_COMMAND requires payload object"

        for k in ("intent", "operation", "output"):
            if k not in payload:
                return False, f"K9_COMMAND.payload missing field: {k}"

        # Intent duplication rule
        if payload.get("intent") != obj.get("intent"):
            return False, "Top-level intent and payload.intent must match"

        if "filters" in payload and not isinstance(payload.get("filters"), dict):
            return False, "K9_COMMAND.payload.filters must be an object"
        if payload.get("time") is not None and not isinstance(payload.get("time"), dict):
            return False, "K9_COMMAND.payload.time must be an object if provided"

        return True, "OK"

    if out_type == "COMPOSITE_K9_COMMAND":
        return validate_composite_llm_output_schema(obj)

    # CLARIFICATION_REQUEST
    reason = obj.get("reason")
    options = obj.get("options")
    if not reason:
        return False, "CLARIFICATION_REQUEST missing field: reason"
    if not isinstance(options, list) or len(options) == 0:
        return False, "CLARIFICATION_REQUEST requires non-empty options list"
    if len(options) > 3:
        return False, "CLARIFICATION_REQUEST options must be <= 3"

    for i, opt in enumerate(options):
        if not isinstance(opt, dict):
            return False, f"CLARIFICATION_REQUEST.options[{i}] must be an object"
        if "label" not in opt or "description" not in opt:
            return False, f"CLARIFICATION_REQUEST.options[{i}] missing label/description"

    return True, "OK"


def validate_composite_llm_output_schema(obj: Dict) -> Tuple[bool, str]:
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

        for k in ("intent", "operation", "output"):
            if k not in payload:
                return False, f"plan[{i}].payload missing field: {k}"

        # Intent duplication rule inside composite
        if payload.get("intent") != step.get("intent"):
            return False, f"plan[{i}] top-level intent and payload.intent must match"

    return True, "OK"
