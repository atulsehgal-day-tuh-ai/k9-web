import sys
import os

# ============================================
# CONFIGURAR PYTHONPATH PARA IMPORTAR EL PROYECTO
# ============================================

# Calcular carpeta raíz del proyecto: k9_mining_safety/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agregar la carpeta raíz al PYTHONPATH → permite importar config/
sys.path.append(ROOT_DIR)

# Agregar la carpeta src/ al PYTHONPATH → permite importar graph/, state/, nodes/
SRC_DIR = os.path.join(ROOT_DIR, "src")
sys.path.append(SRC_DIR)

# ============================================
# IMPORTAR EL GRAFO Y EL ESTADO
# ============================================
from graph.main_graph import build_k9_graph
from state.state import K9State


# ============================================
# TEST PRINCIPAL DEL PIPELINE
# ============================================
def test():
    graph = build_k9_graph()

    # PRUEBA: modificar esta línea para probar diferentes queries
    result = graph.invoke(K9State(user_query="hola"))

    print(result)


if __name__ == "__main__":
    test()
