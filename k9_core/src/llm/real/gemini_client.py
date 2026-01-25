# src/llm/real/gemini_client.py
from __future__ import annotations

import json
import os
import re
from typing import Optional

from google import genai

from src.llm.base_client import BaseLLMClient
from src.llm.payload import LLMPayload


class GeminiClient(BaseLLMClient):
    """
    GeminiClient — Infraestructura LLM real para K9

    Responsabilidades:
    - Consumir LLMPayload
    - Enviar prompt a Gemini
    - Retornar texto limpio (JSON string o texto)

    Restricciones:
    - NO razona
    - NO interpreta
    - NO decide flujo
    - NO mantiene estado
    """

    def __init__(self, api_key: Optional[str], model: str):
        if not api_key:
            raise ValueError("Gemini API key no configurada")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    # =====================================================
    # Public API
    # =====================================================
    def generate(self, payload: LLMPayload) -> str:
        """
        Envía el payload renderizado a Gemini y retorna texto plano.

        El parsing semántico ocurre en LLMNode, NO aquí.
        """

        # 🔹 Contrato correcto: el payload sabe cómo renderizarse
        prompt = payload.render()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        raw_text = response.text or ""
        raw_text = raw_text.strip()

        # Intentar extraer JSON limpio si viene envuelto
        extracted = self._extract_json(raw_text)

        return extracted if extracted else raw_text

    # =====================================================
    # Helpers
    # =====================================================
    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extrae el primer bloque JSON válido desde una respuesta LLM.

        Maneja casos comunes:
        - ```json ... ```
        - Texto + JSON
        - JSON plano
        """

        # Caso: fenced block ```json
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1).strip()

        # Caso: primer objeto JSON detectado
        brace = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace:
            candidate = brace.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                return None

        return None
