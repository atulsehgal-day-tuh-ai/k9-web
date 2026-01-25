# src/llm/base_client.py
from __future__ import annotations

from typing import Protocol

from src.llm.payload import LLMPayload


class BaseLLMClient(Protocol):
    """
    BaseLLMClient — K9 v1.0

    Contrato mínimo que todo cliente LLM debe cumplir.
    (Mock, OpenAI, Gemini, local, etc.)

    ❗ No guarda estado
    ❗ No conoce K9State
    ❗ No decide flujo
    ❗ No interpreta intención
    """

    def generate(self, payload: LLMPayload) -> str:
        """
        Ejecuta una llamada LLM usando un payload completamente
        definido por K9 y retorna solo texto.

        El contenido y la autoridad semántica
        vienen EXCLUSIVAMENTE desde el payload.
        """
        ...
