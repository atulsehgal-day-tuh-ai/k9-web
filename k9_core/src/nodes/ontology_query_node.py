import yaml
from pathlib import Path
from typing import Dict, List, Any

from src.state.state import K9State


class OntologyQueryNode:
    """
    K9 Mining Safety
    OntologyQueryNode

    Nodo determinista para consultas ONTOLOGY_QUERY.
    Lee exclusivamente archivos YAML ontológicos.
    """

    def __init__(self, ontology_path: str):
        self.ontology_path = Path(ontology_path)

        # ---------------------------------------------------------
        # Mapping entity -> YAML files (ontología real)
        # ---------------------------------------------------------
        self.entity_to_yaml = {
            "risk": ["01_catalogo_riesgos_v8.yaml"],
            "controls": ["02_catalogo_controles_v6.yaml"],
            "causes": ["03_catalogo_causas_v4.yaml"],
            "consequences": ["04_catalogo_consecuencias_v6.yaml"],
            "degradation_factors": ["05_catalogo_factores_degradacion_v3.yaml"],
            "recovery_barriers": ["06_catalogo_barreras_recuperacion_v3.yaml"],
            "bowtie": [
                "07_bowtie_caida_altura_v3.yaml",
                "08_bowtie_caida_objetos_v3.yaml",
                "09_bowtie_contacto_energia_v3.yaml",
            ],
            "roles": ["10_catalogo_roles_v3.yaml"],
            "tasks": ["12_catalogo_tareas_v1.yaml"],
            "areas": ["13_catalogo_areas_operacionales_v1.yaml"],
            "ppe": ["14_catalogo_epp_v3.yaml"],
            "hazards": ["17_catalogo_peligros_detectados_v5.yaml"],
            "corrective_actions": ["19_catalogo_acciones_correctivas_v1.yaml"],
        }

        # ---------------------------------------------------------
        # entity x operation matrix (Canon v1.2 — Fase 3)
        # ---------------------------------------------------------
        self.allowed_operations = {
            "risk": {
                "retrieve",
                "describe",
                "get_causes",
                "get_controls",
                "get_consequences",
                "get_tasks_and_roles",
            },
            "controls": {"retrieve", "describe"},
            "causes": {"retrieve", "describe"},
            "consequences": {"retrieve", "describe"},
            "degradation_factors": {"retrieve", "describe"},
            "recovery_barriers": {"retrieve", "describe"},
            "bowtie": {"retrieve"},
            "roles": {"retrieve", "describe"},
            "tasks": {"retrieve", "describe"},
            "areas": {"retrieve", "describe"},
            "ppe": {"retrieve", "describe"},
            "hazards": {"retrieve", "describe"},
            "corrective_actions": {"retrieve", "describe"},
        }

    # ---------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------
    def __call__(self, state: K9State) -> K9State:
        command = (state.context_bundle or {}).get("k9_command", {})

        state.context_bundle = state.context_bundle or {}
        state.reasoning = state.reasoning or []

        try:
            execution_result = self._execute(command)

            state.context_bundle["ontology_result"] = {
                "type": "ontology_result",
                "entity": command.get("entity"),
                "operation": command.get("operation"),
                "payload": execution_result["payload"],
                "traceability": execution_result["traceability"],
            }

            state.reasoning.append(
                f"OntologyQueryNode ejecutado: {command.get('entity')} / {command.get('operation')}"
            )

        except OntologyQueryError as e:
            state.context_bundle["ontology_result"] = self._error_output(e)
            state.reasoning.append(f"OntologyQueryNode error: {e.code}")

        return state

    # ---------------------------------------------------------
    # Core execution
    # ---------------------------------------------------------
    def _execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        intent = command.get("intent")
        entity = command.get("entity")
        operation = command.get("operation")
        filters = command.get("filters", {})

        if intent != "ONTOLOGY_QUERY":
            raise OntologyQueryError(
                "INVALID_INTENT",
                f"OntologyQueryNode received intent '{intent}'",
            )

        if entity not in self.entity_to_yaml:
            raise OntologyQueryError(
                "ONTOLOGY_ENTITY_NOT_SUPPORTED",
                f"Entity '{entity}' not supported",
                {"entity": entity},
            )

        if operation not in self.allowed_operations.get(entity, set()):
            raise OntologyQueryError(
                "ONTOLOGY_OPERATION_NOT_ALLOWED",
                f"Operation '{operation}' not allowed for entity '{entity}'",
                {"entity": entity, "operation": operation},
            )

        # ---------------------------------------------------------
        # Familia B — risk → causes
        # ---------------------------------------------------------
        if entity == "risk" and operation == "get_causes":
            risk_id = filters.get("risk_id")
            if not risk_id:
                raise OntologyQueryError("ONTOLOGY_ID_REQUIRED", "risk_id required")

            causes, source_files = self._load_yaml_files("causes")

            matched = [
                c for c in causes if c.get("riesgo_asociado") == risk_id
            ]

            if not matched:
                raise OntologyQueryError(
                    "ONTOLOGY_RELATION_NOT_FOUND",
                    f"No causes found for risk '{risk_id}'",
                )

            return {
                "payload": {
                    "source_id": risk_id,
                    "related_entities": matched,
                },
                "traceability": {
                    "source_files": source_files,
                    "filters_applied": filters,
                    "resolution_path": [f"causes.riesgo_asociado == {risk_id}"],
                },
            }

        # ---------------------------------------------------------
        # Bowtie — retrieve completo
        # ---------------------------------------------------------
        if entity == "bowtie" and operation == "retrieve":
            risk_id = filters.get("risk_id")
            if not risk_id:
                raise OntologyQueryError("ONTOLOGY_ID_REQUIRED", "risk_id required")

            bowties, source_files = self._load_yaml_files("bowtie")

            for bowtie in bowties:
                if bowtie.get("riesgo", {}).get("id") == risk_id:
                    return {
                        "payload": {"bowtie": bowtie},
                        "traceability": {
                            "source_files": source_files,
                            "filters_applied": filters,
                            "resolution_path": [f"bowtie.riesgo.id == {risk_id}"],
                        },
                    }

            raise OntologyQueryError(
                "ONTOLOGY_RELATION_NOT_FOUND",
                f"No bowtie found for risk '{risk_id}'",
            )

        # ---------------------------------------------------------
        # Familia C — risk → tasks → roles
        # ---------------------------------------------------------
        if entity == "risk" and operation == "get_tasks_and_roles":
            risk_id = filters.get("risk_id")
            if not risk_id:
                raise OntologyQueryError("ONTOLOGY_ID_REQUIRED", "risk_id required")

            tasks, _ = self._load_yaml_files("tasks")

            matched_tasks = []
            roles = set()

            for task in tasks:
                if risk_id in task.get("riesgos_asociados", []):
                    matched_tasks.append(task["id"])
                    if task.get("id_rol"):
                        roles.add(task["id_rol"])

            if not matched_tasks:
                raise OntologyQueryError(
                    "ONTOLOGY_RELATION_NOT_FOUND",
                    f"No tasks found for risk '{risk_id}'",
                )

            return {
                "payload": {
                    "source_id": risk_id,
                    "tasks": matched_tasks,
                    "roles": sorted(roles),
                },
                "traceability": {
                    "source_files": ["12_catalogo_tareas_v1.yaml"],
                    "filters_applied": filters,
                    "resolution_path": [f"tasks.riesgos_asociados contains {risk_id}"],
                },
            }

        # ---------------------------------------------------------
        # Familia B genérica (ej. get_controls)
        # ---------------------------------------------------------
        yaml_data, source_files = self._load_yaml_files(entity)

        payload, resolution_path = self._resolve_operation(
            entity, operation, yaml_data, filters
        )

        return {
            "payload": payload,
            "traceability": {
                "source_files": source_files,
                "filters_applied": filters,
                "resolution_path": resolution_path,
            },
        }

    # ---------------------------------------------------------
    # YAML loading
    # ---------------------------------------------------------
    def _load_yaml_files(self, entity: str):
        data = []
        source_files = []

        for filename in self.entity_to_yaml[entity]:
            path = self.ontology_path / filename
            if not path.exists():
                continue

            with open(path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if isinstance(content, list):
                    data.extend(content)
                else:
                    data.append(content)

            source_files.append(filename)

        if not data:
            raise OntologyQueryError(
                "ONTOLOGY_SOURCE_NOT_FOUND",
                f"No data found for entity '{entity}'",
            )

        return data, source_files

    # ---------------------------------------------------------
    # Operation resolution (Familia B simple)
    # ---------------------------------------------------------
    def _resolve_operation(
        self,
        entity: str,
        operation: str,
        data: List[Dict[str, Any]],
        filters: Dict[str, Any],
    ):
        if entity == "risk" and operation == "get_controls":
            risk_id = filters.get("risk_id")
            risk = next((r for r in data if r.get("id") == risk_id), None)

            if not risk:
                raise OntologyQueryError(
                    "ONTOLOGY_ENTITY_NOT_FOUND",
                    f"Risk '{risk_id}' not found",
                )

            controls = risk.get("controles_criticos", [])
            if not controls:
                raise OntologyQueryError(
                    "ONTOLOGY_RELATION_NOT_FOUND",
                    f"No controls for risk '{risk_id}'",
                )

            return (
                {"source_id": risk_id, "controls": controls},
                [f"risk.id == {risk_id} → controles_criticos"],
            )

        raise OntologyQueryError(
            "ONTOLOGY_OPERATION_NOT_IMPLEMENTED",
            f"Operation '{operation}' not implemented",
        )

    # ---------------------------------------------------------
    # Error output
    # ---------------------------------------------------------
    def _error_output(self, error: "OntologyQueryError"):
        return {
            "type": "ontology_error",
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            },
            "traceability": {
                "source_files": [],
                "filters_applied": {},
            },
        }


class OntologyQueryError(Exception):
    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
