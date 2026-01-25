from src.graph.main_graph import build_k9_graph

g = build_k9_graph()
result = g.invoke({"user_query": "hola"})
print(result)
