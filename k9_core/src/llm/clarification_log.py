from __future__ import annotations

from typing import Dict, Any
from datetime import datetime
import json
import pathlib


class ClarificationLog:
    """
    Registro permanente de solicitudes de clarificación del LLM.
    Append-only.
    """

    def __init__(self, path: str = "logs/clarifications.jsonl"):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        session_id: str,
        turn_index: int,
        user_question: str,
        reason: str,
        options: list,
        raw_llm_output: Dict[str, Any],
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn_index": turn_index,
            "user_question": user_question,
            "reason": reason,
            "options": options,
            "llm_output": raw_llm_output,
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ======================================================
# Compatibility adapter for LLMNode
# ======================================================

_default_log = ClarificationLog()


def log_clarification_event(event: Dict[str, Any]) -> None:
    """
    Adapter function expected by LLMNode.

    Translates generic clarification events into
    the structured ClarificationLog.record() format.
    """
    try:
        _default_log.record(
            session_id=event.get("session_id", "unknown"),
            turn_index=event.get("turn_index", -1),
            user_question=event.get("user_question", ""),
            reason=event.get("reason", ""),
            options=event.get("options", []),
            raw_llm_output=event.get("raw_llm_output", {}),
        )
    except Exception:
        # Logging must NEVER break execution
        pass

