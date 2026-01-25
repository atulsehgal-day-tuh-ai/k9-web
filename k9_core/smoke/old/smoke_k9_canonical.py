"""
K9 Mining Safety
Canonical Smoke Test – Pre-LLM

Objetivo:
- Validar ejecución determinista del sistema K9
- Sin lenguaje natural
- Sin LLM
- Sin inferencias implícitas
"""

from src.state.state import K9State
from src.router.router import route_state


# ==========================================================
# Helper: ejecutar comando canónico
# ==========================================================

def run_k9_command(command: dict, label: str):
    print("\n" + "=" * 80)
    print(f"SMOKE CASE: {label}")
    print("- Command:")
    print(command)

    state = K9State(
        user_query=None,
        intent=command["intent"],
        analysis={},
        reasoning=[],
        demo_mode=True,
        context_bundle={
            "k9_command": command
        },
    )

    final_state = route_state(state)

    print("- Final intent:", final_state.intent)
    print("- Reasoning:")
    for r in final_state.reasoning:
        print("  •", r)

    if final_state.analysis:
        print("- Analysis keys:", list(final_state.analysis.keys()))

    if final_state.answer:
        print("- Narrative output:")
        print(final_state.answer)

    return final_state


# ==========================================================
# CANONICAL SMOKE TESTS
# ==========================================================

def test_01_risk_ranking_current_week():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "rank",
            "time": {"type": "relative", "value": "current_week"},
            "output": "analysis",
        },
        label="01 – Risk ranking (current week)",
    )


def test_02_risk_underestimated_by_proactive():
    return run_k9_command(
        {
            "intent": "COMPARATIVE_QUERY",
            "entity": "risks",
            "operation": "compare",
            "filters": {
                "model": "proactive_model",
                "baseline": "K9",
            },
            "time": {"type": "relative", "value": "last_weeks"},
            "output": "analysis",
        },
        label="02 – Risk underestimated by proactive model",
    )


def test_03_risk_evolution_r02():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "evolution",
            "filters": {"risk_id": ["R02"]},
            "time": {"type": "relative", "value": "last_4_weeks"},
            "output": "analysis",
        },
        label="03 – Risk evolution R02",
    )


def test_04_signals_pre_critical_monday():
    return run_k9_command(
        {
            "intent": "TEMPORAL_RELATION_QUERY",
            "entity": "signals",
            "operation": "sequence",
            "filters": {"anchor_event": "CRITICAL_MONDAY"},
            "time": {"type": "window", "value": "pre_post"},
            "output": "analysis",
        },
        label="04 – Signals before critical Monday",
    )


def test_05_observations_last_week():
    return run_k9_command(
        {
            "intent": "OPERATIONAL_QUERY",
            "entity": "observations",
            "operation": "summarize",
            "time": {"type": "relative", "value": "last_week"},
            "output": "raw",
        },
        label="05 – Observations last week",
    )


def test_06_operational_pressure_ranking():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "rank",
            "filters": {"metric": "operational_pressure"},
            "time": {"type": "relative", "value": "current_period"},
            "output": "analysis",
        },
        label="06 – Operational pressure ranking",
    )


def test_07_explain_proactive_vs_k9_r01():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "explain",
            "filters": {
                "risk_id": ["R01"],
                "comparison": "proactive_vs_k9",
            },
            "time": {"type": "relative", "value": "last_month"},
            "output": "analysis",
        },
        label="07 – Explain proactive vs K9 (R01)",
    )


def test_08_monthly_risk_summary():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "summarize",
            "time": {"type": "relative", "value": "last_month"},
            "output": "analysis",
        },
        label="08 – Monthly risk narrative (structured)",
    )


def test_09_threshold_crossing():
    return run_k9_command(
        {
            "intent": "ANALYTICAL_QUERY",
            "entity": "risks",
            "operation": "detect_threshold_crossing",
            "filters": {"threshold": "critical"},
            "time": {"type": "relative", "value": "last_weeks"},
            "output": "analysis",
        },
        label="09 – Critical threshold crossing",
    )


def test_10_ontology_exposure_r01():
    return run_k9_command(
        {
            "intent": "ONTOLOGY_QUERY",
            "entity": "risk",
            "operation": "get_tasks_and_roles",
            "filters": {"risk_id": "R01"},
            "output": "raw",
        },
        label="10 – Ontology exposure (tasks & roles R01)",
    )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    test_01_risk_ranking_current_week()
    test_02_risk_underestimated_by_proactive()
    test_03_risk_evolution_r02()
    test_04_signals_pre_critical_monday()
    test_05_observations_last_week()
    test_06_operational_pressure_ranking()
    test_07_explain_proactive_vs_k9_r01()
    test_08_monthly_risk_summary()
    test_09_threshold_crossing()
    test_10_ontology_exposure_r01()

    print("\n✅ K9 Canonical Smoke Test completed successfully.")
