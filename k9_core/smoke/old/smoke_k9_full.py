from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.graph.main_graph import build_k9_graph
from src.state.state import K9State


def run_smoke(graph, question: str, must_contain=None, must_not_contain=None):
    print("\n" + "=" * 80)
    print("Q:", question)

    state = K9State(
        user_query=question,
        intent="",
        analysis={},
        reasoning=[],
        demo_mode=True,  # smoke siempre en modo demo determinista
    )

    result = graph.invoke(state)

    # LangGraph puede devolver dict o estado
    answer = result.get("answer", "") if isinstance(result, dict) else result.answer
    reasoning = result.get("reasoning", []) if isinstance(result, dict) else result.reasoning

    print("ANSWER:")
    print(answer)
    print("\nREASONING:")
    for r in reasoning:
        print("-", r)

    if must_contain:
        for token in must_contain:
            assert token.lower() in answer.lower(), f"Missing token: {token}"

    if must_not_contain:
        for token in must_not_contain:
            assert token.lower() not in answer.lower(), f"Forbidden token: {token}"

    return result


def main():
    graph = build_k9_graph()

    # 1. Riesgo dominante
    run_smoke(
        graph,
        "¿Cuál es el riesgo más importante esta semana y por qué?",
        must_contain=["R02"]
    )

    # 2. Riesgo subestimado por el modelo proactivo
    run_smoke(
        graph,
        "¿Existe algún riesgo que esté siendo subestimado por el modelo proactivo?",
        must_contain=["proactivo"]
    )

    # 3. Evolución temporal de un riesgo
    run_smoke(
        graph,
        "Muéstrame cómo ha evolucionado la Caída de Objetos (R02) en las últimas semanas",
        must_contain=["R02"]
    )

    # 4. Señales previas al lunes crítico
    run_smoke(
        graph,
        "¿Qué señales aparecieron antes del lunes crítico?",
        must_contain=["lunes"]
    )

    # 5. Observaciones última semana
    run_smoke(
        graph,
        "¿Cuántas observaciones se registraron la semana pasada y de qué tipo?",
        must_contain=["observ"]
    )

    # 6. Presión operacional
    run_smoke(
        graph,
        "¿Qué riesgos presentan la mayor presión operacional?",
        must_contain=["R02"]
    )

    # 7. Ranking proactivo vs K9
    run_smoke(
        graph,
        "¿Por qué el ranking del modelo proactivo no refleja completamente el riesgo emergente R01?",
        must_contain=["proactivo"]
    )

    # 8. Narrativa mensual
    run_smoke(
        graph,
        "Dame un análisis narrativo del último mes para los principales riesgos",
        must_contain=["R02"]
    )

    # 9. Umbral crítico
    run_smoke(
        graph,
        "¿Qué riesgos han superado el umbral crítico?",
        must_contain=["R02"]
    )

    # 10. Fuera de dominio
    result = run_smoke(
        graph,
        "¿Cuál es la capital de Chile?",
        must_not_contain=["santiago", "chile es", "capital"]
    )

    # Validación cognitiva del rechazo
    reasoning_text = " ".join(
        result.get("reasoning", [])
        if isinstance(result, dict)
        else result.reasoning
    ).lower()

    assert (
        "fuera de dominio" in reasoning_text
        or "out_of_domain" in reasoning_text
        or "fallback" in reasoning_text
    ), "Expected out-of-domain reasoning not found"

    print("\n✅ ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
