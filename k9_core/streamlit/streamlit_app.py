import sys
import os

# --------------------------------------------------
# Ajuste de path para importar src (igual que tests)
# --------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)


import uuid
import streamlit as st
import plotly.graph_objects as go


# ===============================
# Import motor K9
# ===============================
from src.graph.main_graph import build_k9_graph
from src.state.state import K9State

# ===============================
# Import Metrics Adapter
# ===============================
from src.ui_adapters.metrics_adapter import render_metrics



# --------------------------------------------------
# Construcción del grafo (UNA sola vez)
# --------------------------------------------------
GRAPH = build_k9_graph()

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="K9 Mining Safety", layout="wide")

# ============================================================
# CSS — preservar estética del mockup
# ============================================================
st.markdown(
    """
<style>
    .block-container {
        max-width: 800px;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .main-block {
        padding-bottom: 90px;
    }
    .user-bubble {
        background-color: #444;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 6px;
        display: inline-block;
        max-width: 85%;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# ESTADO DE SESIÓN
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🛡️ K9 Mining Safety")
    st.markdown("Cognitive Safety System")
    st.markdown("---")
    st.markdown(f"**Session:** `{st.session_state.session_id}`")

# ============================================================
# HELPERS
# ============================================================
def format_reasoning(reasoning):
    if not reasoning:
        return "reasoning: []"
    return "\n".join(["reasoning:"] + [f"  - {r}" for r in reasoning])

# ============================================================
# EJECUCIÓN DEL GRAFO
# ============================================================
def run_k9(query: str) -> dict:
    initial_state = K9State(user_query=query)
    return GRAPH.invoke(initial_state)

# ============================================================
# HISTORIAL DEL CHAT
# ============================================================
st.markdown('<div class="main-block">', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-bubble"><strong>Pregunta:</strong> {msg["content"]}</div>',
            unsafe_allow_html=True,
        )
        continue

    with st.expander("Ver reasoning (nodo cognitivo)"):
        st.code(format_reasoning(msg.get("reasoning")), language="yaml")

    st.markdown(f"**Respuesta:** {msg.get('content', '')}")

    # -------- Visualizaciones sugeridas (via adapter) --------
    visual_suggestions = msg.get("metrics", [])
    analysis = msg.get("analysis", {})

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    for j, artifact in enumerate(rendered):
        label = visual_suggestions[j].get("question", "Ver visualización")

        if st.button(label, key=f"viz_{i}_{j}"):
            if artifact["type"] == "plotly":
                st.plotly_chart(
                    artifact["figure"],
                    use_container_width=True,
                )
            elif artifact["type"] == "table":
                st.dataframe(artifact["data"])

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# INPUT FIJO ABAJO
# ============================================================
query = st.chat_input("Escribe tu pregunta:")

if query:
    st.session_state.messages.append(
        {"role": "user", "content": query.strip()}
    )

    with st.spinner("Procesando razonamiento cognitivo..."):
        result = run_k9(query.strip())

    analysis = result.get("analysis", {}) or {}

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "reasoning": result.get("reasoning", []),
            "metrics": analysis.get("metrics", {}).get("visual_suggestions", []),
            "analysis": analysis,
        }
    )

    st.rerun()
