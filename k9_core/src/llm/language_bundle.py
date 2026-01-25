# src/llm/language_bundle.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


# ======================================================
# K9 Language Bundle Paths (OFICIAL)
# ======================================================
LANGUAGE_DIR = Path(__file__).resolve().parents[1] / "language"

SCHEMA_PATH = LANGUAGE_DIR / "k9_canonical_schema_v1_2.json"
LANGUAGE_PATH = LANGUAGE_DIR / "k9_language_v1_1.json"
ONTOLOGY_OPS_PATH = LANGUAGE_DIR / "k9_ontology_operations_v1_2.json"
EXAMPLES_BASIC_PATH = LANGUAGE_DIR / "k9_examples_basic.json"
EXAMPLES_ADVANCED_PATH = LANGUAGE_DIR / "k9_examples_advanced.json"
DOMAIN_SEMANTICS_ES_PATH = LANGUAGE_DIR / "k9_domain_semantics_es.json"
META_REASONING_EXAMPLES_PATH = LANGUAGE_DIR / "k9_meta_examples_reasoning_v0.json"

# ======================================================
# Internal cache
# ======================================================
_BUNDLE_CACHE: Optional[Dict[str, Any]] = None


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"K9 language file not found: {path.as_posix()}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_k9_language_bundle(force_reload: bool = False) -> Dict[str, Any]:
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
        "meta_reasoning_examples": _load_json(META_REASONING_EXAMPLES_PATH),
        "domain_semantics_es": _load_json(DOMAIN_SEMANTICS_ES_PATH),
    }

    _BUNDLE_CACHE = bundle
    return bundle
