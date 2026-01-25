# run_fase1_smoke.py

from src.graph.main_graph import build_k9_graph
from src.state.state import K9State


def run_fase1_question(question: str):
    # Construcción del grafo FASE 1
    graph = build_k9_graph()

    # Estado inicial
    state = K9State(
        user_query=question
    )

    # Ejecución del grafo
    result = graph.invoke(state)

    # LangGraph puede devolver dict o K9State
    final_state = (
        result if isinstance(result, K9State)
        else K9State(**result)
    )

    # ------------------------------------------------------------
    # OUTPUT CONTROLADO (FASE 1)
    # ------------------------------------------------------------
    print("\n==============================")
    print("USER QUESTION")
    print("==============================")
    print(question)

    print("\n==============================")
    print("ANALYSIS (structured)")
    print("==============================")

    if not final_state.analysis:
        print("[WARN] analysis vacío")
    else:
        for k, v in final_state.analysis.items():
            print(f"\n--- {k} ---")
            print(v)

    print("\n==============================")
    print("ANSWER (narrative)")
    print("==============================")
    print(final_state.answer or "[NO ANSWER]")

    print("\n==============================")
    print("REASONING TRACE")
    print("==============================")

    if not final_state.reasoning:
        print("[WARN] reasoning vacío")
    else:
        for r in final_state.reasoning:
            print("-", r)


if __name__ == "__main__":
    #run_fase1_question(
    #    "¿Cuál es el riesgo dominante hoy y cuál es el que más preocupa?"
    #)
    #run_fase1_question(
    #"¿Hay algún elemento que esté empeorando progresivamente en las últimas semanas?"
    #)
    #run_fase1_question(
    #"¿Cuál es el riesgo dominante actualmente y cuál es el que debería preocupar más por su tendencia?"
    #)
    #run_fase1_question(
    #"¿Hay algún riesgo que el modelo proactivo esté subestimando?"
    #)
    #run_fase1_question(
    #"¿Qué tipo de observaciones se han registrado en las últimas semanas y cómo han evolucionado?"
    #)
    #run_fase1_question(
    #"¿Qué riesgos tienen evidencia operacional reciente?"
    #)
    #run_fase1_question(
    #"¿Existe alguna desalineación entre el modelo proactivo y el análisis K9 para los riesgos actuales?"
    #)
    #run_fase1_question(
    #"¿Qué riesgos deberían preocupar más si el modelo proactivo se equivoca?"
    #)
    run_fase1_question(
    "¿Si el modelo proactivo subestima algún riesgo, ¿cuál debería priorizarse preventivamente y por qué?"
    )