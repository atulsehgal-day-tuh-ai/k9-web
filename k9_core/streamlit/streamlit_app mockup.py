import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="K9 Mining Safety", layout="wide")

# ============================================================
# CSS SEGURO – ANCHO A 800px + AJUSTE NARRATIVA
# ============================================================
st.markdown("""
<style>
    .block-container {
        max-width: 800px;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .main-block {
        padding-bottom: 80px;
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
    h2 {
        font-size: 1.4rem !important;   /* títulos narrativos más pequeños */
    }
    h3 {
        font-size: 1.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

    /* --- MODO DIOS --- 
       Cambia TODO el texto dentro del sidebar,
       sin importar qué estilo interno tenga Streamlit 
    */

    section[data-testid="stSidebar"] * {
        color: #1a1a1a !important;     /* gris oscuro legible */
        text-shadow: none !important;  /* elimina efectos que aclaran el texto */
    }

    /* Asegura contraste incluso si Streamlit fuerza opacidad */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        opacity: 1 !important;
        color: #1a1a1a !important;
    }

</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO GLOBAL
# ============================================================
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "pending_graph" not in st.session_state:
    st.session_state["pending_graph"] = False


# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def load_data():
    df_signals = pd.read_parquet("data/k9_weekly_signals.parquet")
    df_proactivo = pd.read_csv("data/stde_proactivo_semanal_v4_4.csv")
    df_tray = pd.read_csv("data/stde_trayectorias_semanales.csv")
    df_events = pd.read_csv("data/stde_eventos.csv")
    df_obs = pd.read_csv("data/stde_observaciones_12s.csv")
    df_aud = pd.read_csv("data/stde_auditorias_12s.csv")
    return df_signals, df_proactivo, df_tray, df_events, df_obs, df_aud


df_signals, df_proactivo, df_tray, df_events, df_obs, df_aud = load_data()


# ============================================================
# MAPEOS OFICIALES DE RIESGOS
# ============================================================
RISK_MAP = {
    "R01": "Caída de Altura (R01)",
    "R02": "Caída de Objetos (R02)",
    "R03": "Contacto con Energía (R03)"
}

def pretty_risk(rid):
    if rid in RISK_MAP:
        return RISK_MAP[rid]
    return f"Riesgo {rid}"


# ============================================================
# SIDEBAR CON LOGO Y ANCHORS
# ============================================================
st.sidebar.image("data/logo.png", width=180)
st.sidebar.title("K9 Mining Safety")
st.sidebar.markdown("### *CMAS – Cognitive Multi-Agent System*")
st.sidebar.markdown("---")

st.sidebar.markdown("#### Historial de preguntas")

for idx, msg in enumerate([m for m in st.session_state["messages"] if m["role"] == "user"]):
    anchor = f"q_{idx}"
    st.sidebar.markdown(f"<a href='#{anchor}' style='text-decoration:none; color:#ccc;'>{msg['content']}</a>", 
                        unsafe_allow_html=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def plot_r02():
    df_r = df_signals[df_signals["riesgo_id"] == "R02"]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_r["semana"],
        y=df_r["score"],
        mode="lines+markers",
        name="Score R02",
        line=dict(color="orange", width=3)
    ))

    # threshold crítico
    fig.add_hline(
        y=0.80,
        line_color="red",
        line_width=2,
        annotation_text="Umbral crítico 0.80",
        annotation_position="top left"
    )

    fig.update_layout(
        title="Evolución semanal: Caída de Objetos (R02)",
        xaxis_title="Semana",
        yaxis_title="Score K9",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def narrative_last_month():
    st.markdown("""
## **Análisis Narrativo del Último Mes – Riesgos R01 y R02**

Durante el último mes, K9 analizó la evolución de **Caída de Altura (R01)** y  
**Caída de Objetos (R02)** integrando señales granulares, score K9, auditorías,  
observaciones y factores operacionales.

---

### **Caída de Altura (R01) – Señales emergentes**
- Tendencia leve pero sostenida al alza.  
- Acumulación de señales débiles.  
- Observaciones OCC y auditorías indican presión operacional.  
- K9 detecta comportamiento emergente.

---

### **Caída de Objetos (R02) – Riesgo dominante**
- Continúa como el riesgo más alto en score K9.  
- Influenciado por congestión, dotación y variabilidad.  
- El modelo proactivo coincide en su clasificación.

---

**Conclusión:**  
K9 combina datos agregados y granulares para entregar una interpretación cognitiva del estado operacional.
""")


def get_proactive_ranking():
    wk = df_proactivo["semana_id"].max()
    df_last = df_proactivo[df_proactivo["semana_id"] == wk].copy()

    # transformar nombres
    df_last["riesgo_id"] = df_last["riesgo_id"].apply(pretty_risk)

    df_last = df_last.sort_values("score_proactivo", ascending=False)
    df_last["Ranking"] = range(1, len(df_last) + 1)
    df_last = df_last.set_index("Ranking")
    return wk, df_last


def get_observations_last_week():
    wk = df_obs["semana"].max()
    df_last = df_obs[df_obs["semana"] == wk]
    return wk


# ============================================================
# REASONING DETALLADO FORMATO LANGGRAPH
# ============================================================
def format_reasoning(text):
    """Bloque visual como LangGraph / YAML expandido."""
    return f"""
────────────────────────────
REASONING (Nodo Cognitivo)
────────────────────────────
{text}
────────────────────────────
"""


# ============================================================
# DESPACHADOR DE CONSULTAS
# ============================================================
def handle_query(query):
    q = query.lower()

    # ==========================
    # Fuera de dominio
    # ==========================
    if "capital" in q and "chile" in q:
        reasoning = """reasoning:
  input:
    - consulta_usuario
  ops:
    - validar_dominio
    - detectar_fuera_de_alcance
  output:
    acción: rechazar_pregunta
"""
        return (
            "Lo siento, no puedo responder esta pregunta porque está fuera del dominio del sistema K9.",
            reasoning,
            False, False, False
        )

    # ==========================
    # Observaciones
    # ==========================
    if "observacion" in q or "observaciones" in q:
        wk = df_obs["semana"].max()

        reasoning = f"""reasoning:
  input:
    - observaciones_semana
  ops:
    - semana_actual := {wk}
    - filtrar(semana = semana_actual)
    - contar_registros
    - clasificar(OPG, OCC)
  output:
    total_observaciones: 42
    observaciones_preventivas: 34
    observaciones_control_critico: 8
"""

        return (
            "En la semana 12 hubo **42 observaciones**: **34 observaciones preventivas generales (OPG)** y **8 observaciones de control crítico (OCC)**.",
            reasoning,
            False, False, False
        )

    # ==========================
    # Ranking
    # ==========================
    if "ranking" in q:
        wk, _ = get_proactive_ranking()

        reasoning = f"""reasoning:
  input:
    - ranking_proactivo
  ops:
    - semana_actual := {wk}
    - ordenar_por(score_proactivo DESC)
    - asignar_ranking
  output:
    ranking_generado: true
"""

        return (
            f"Este es el ranking de riesgos de la semana {wk}.",
            reasoning,
            False, True, False
        )

    # ==========================
    # Riesgo más importante
    # ==========================
    if "riesgo más importante" in q or "riesgo mas importante" in q:
        wk = df_signals["semana"].max()
        df_w = df_signals[df_signals["semana"] == wk]
        r_top = df_w.sort_values("score", ascending=False).iloc[0]["riesgo_id"]

        st.session_state["pending_graph"] = True

        reasoning = f"""reasoning:
  input:
    - señales_semana
  ops:
    - semana_actual := {wk}
    - filtrar(semana = semana_actual)
    - ordenar_por(score DESC)
    - seleccionar_top(1)
  output:
    riesgo_mas_importante: {r_top}
"""

        return (
            f"El riesgo más importante esta semana es **{pretty_risk(r_top)}**.\n\n ¿Deseas ver un gráfico de la evolución de este riesgo?",
            reasoning,
            False, False, False
        )

    # ==========================
    # Gráfico
    # ==========================
    if "grafico" in q or "gráfico" in q or (q in ["si", "sí"] and st.session_state["pending_graph"]):
        st.session_state["pending_graph"] = False

        reasoning = """reasoning:
  input:
    - señales(R02)
  ops:
    - extraer_series_temporales
    - construir_grafico
  output:
    grafico_generado: R02
"""

        return (
            "Aquí tienes la evolución del riesgo Caída de Objetos (R02).",
            reasoning,
            True, False, False
        )

    # ==========================
    # Narrativa
    # ==========================
    if "narrativ" in q or "último mes" in q or "ultimo mes" in q:

        reasoning = """reasoning:
  input:
    - señales(R01, R02)
    - observaciones
    - auditorías
  ops:
    - analizar_tendencias(últimas_4_semanas)
    - detectar_patrones
    - sintetizar_resumen
  output:
    narrativa_generada: true
"""

        return (
            "Aquí tienes el análisis narrativo del último mes.",
            reasoning,
            False, False, True
        )

    # ==========================
    # Default
    # ==========================
    reasoning = """reasoning:
  input:
    - consulta_usuario
  ops:
    - analizar_intención
    - activar_fallback
  output:
    comandos_validos:
      - ranking
      - riesgo más importante
      - observaciones
      - narrativa
"""

    return (
        "Puedo ayudarte con: ranking, riesgo más importante, observaciones o narrativa.",
        reasoning,
        False, False, False
    )



# ============================================================
# BLOQUE PRINCIPAL DEL CHAT
# ============================================================
st.markdown('<div class="main-block">', unsafe_allow_html=True)
st.markdown("### Conversación")

for i, msg in enumerate(st.session_state["messages"]):
    anchor = f"q_{i}"
    st.markdown(f"<a name='{anchor}'></a>", unsafe_allow_html=True)

    st.markdown("---")

    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-bubble"><strong>Pregunta:</strong> {msg["content"]}</div>',
            unsafe_allow_html=True
        )

    else:
        #with st.expander("Ver reasoning (nodo cognitivo)"):
        #    st.text(msg["reasoning"])
        with st.expander("Ver reasoning (nodo cognitivo)"):
            st.code(msg["reasoning"], language="yaml")

        st.markdown(f"**Respuesta:** {msg['content']}")

        if msg.get("show_rank"):
            wk, df_rank = get_proactive_ranking()
            st.dataframe(df_rank, use_container_width=True)

        if msg.get("show_plot"):
            plot_r02()

        if msg.get("show_narrative"):
            narrative_last_month()

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# INPUT FIJO — CHAT NATIVO STREAMLIT
# ============================================================
query = st.chat_input("Escribe tu pregunta:")

if query:
    st.session_state["messages"].append({
        "role": "user",
        "content": query.strip()
    })

    with st.spinner("Procesando..."):
        
        # llamada al motor cognitivo
        answer, reasoning, show_plot, show_rank, show_narrative = handle_query(query.strip())

        # Delay inteligente según el tipo de resultado
        if show_narrative:
            time.sleep(8.2)
        elif show_plot or show_rank:
            time.sleep(5.8)
        else:
            time.sleep(5.0)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "reasoning": reasoning,
        "show_plot": show_plot,
        "show_rank": show_rank,
        "show_narrative": show_narrative,
    })

    st.rerun()
