from src.graph.main_graph import build_k9_graph

if __name__ == "__main__":
    graph = build_k9_graph()

    result = graph.invoke({
        "user_query": "¿qué áreas operacionales existen?"
    })

    print(result)
