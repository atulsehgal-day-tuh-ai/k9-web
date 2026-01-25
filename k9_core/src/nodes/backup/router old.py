from src.state.state import K9State

def router_node(state: K9State) -> K9State:
    intent = state.intent

    # Log cognitivo
    state.reasoning.append(f"Router Node: routing intent '{intent}'.")

    # Devolvemos el mismo estado, el router NO modifica nada más
    return state
