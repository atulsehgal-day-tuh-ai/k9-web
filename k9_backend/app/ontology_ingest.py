from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml

from app.config import APISettings
from app.neo4j_client import Neo4jClient, Neo4jConfig


def _bootstrap_k9_core(settings: APISettings) -> Path:
    """
    Mirror the bootstrap logic used by the API service so ontology paths resolve.
    """
    here = Path(__file__).resolve()
    configured = Path(settings.k9_core_dir)
    k9_core_dir = configured.resolve() if configured.is_absolute() else (here.parent / configured).resolve()
    sys.path.insert(0, str(k9_core_dir))
    os.chdir(str(k9_core_dir))
    return k9_core_dir


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _iter_records(obj: Any) -> Iterable[Dict[str, Any]]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        # common wrappers
        for key in ("items", "catalogo", "data", "records"):
            inner = obj.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
        # single record
        if "id" in obj:
            return [obj]  # type: ignore[list-item]
    return []


def _resolve_source_file(ontology_dir: Path, source_file: str) -> Path:
    candidate = ontology_dir / source_file
    if candidate.exists():
        return candidate

    # schema sometimes references older versions (e.g., v2 vs v3); pick best match by prefix
    stem_prefix = source_file.split("_v")[0]
    matches = sorted(ontology_dir.glob(f"{stem_prefix}_v*.yaml"))
    if matches:
        return matches[-1]
    raise FileNotFoundError(f"Cannot resolve source_file={source_file} under {ontology_dir}")


def _split_controls(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    The controles YAML contains multiple types. Split into:
    - ControlCritico (es_critico==true)
    - ControlPreventivo (tipo_control==preventivo and not critical)
    - ControlMitigacion (tipo_control==mitigacion)
    """
    crit: List[Dict[str, Any]] = []
    prev: List[Dict[str, Any]] = []
    mitig: List[Dict[str, Any]] = []
    for r in records:
        tipo = str(r.get("tipo_control", "")).strip().lower()
        if bool(r.get("es_critico")):
            crit.append(r)
        elif tipo == "mitigacion":
            mitig.append(r)
        else:
            # default bucket: preventivo (and any other non-critical controls)
            prev.append(r)
    return crit, prev, mitig


def seed_ontology(*, neo4j: Neo4jClient, ontology_dir: Path, wipe: bool = False) -> Dict[str, Any]:
    schema_path = _resolve_source_file(ontology_dir, "99_schema_neo4j_v7.yaml")
    schema = _load_yaml(schema_path) or {}
    nodes = schema.get("nodes") or []
    relationships = schema.get("relationships") or []

    if wipe:
        neo4j.execute("MATCH (n) DETACH DELETE n")

    # preload records for each label
    label_records: Dict[str, List[Dict[str, Any]]] = {}

    for node_def in nodes:
        if not isinstance(node_def, dict):
            continue
        label = str(node_def.get("label") or "").strip()
        source_file = str(node_def.get("source_file") or "").strip()
        if not label or not source_file:
            continue

        src_path = _resolve_source_file(ontology_dir, source_file)
        raw = _load_yaml(src_path)
        records = list(_iter_records(raw))

        if src_path.name.startswith("02_catalogo_controles_"):
            crit, prev, mitig = _split_controls(records)
            if label == "ControlCritico":
                records = crit
            elif label == "ControlPreventivo":
                records = prev
            elif label == "ControlMitigacion":
                records = mitig

        label_records[label] = records

    # constraints
    for label in label_records.keys():
        neo4j.execute(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{label}`) REQUIRE n.id IS UNIQUE")

    # upsert nodes
    node_count = 0
    for label, records in label_records.items():
        if not records:
            continue
        cypher = f"""
UNWIND $rows AS row
MERGE (n:`{label}` {{id: row.id}})
SET n += row.props
"""
        rows = []
        for r in records:
            rid = r.get("id")
            if not isinstance(rid, str) or not rid.strip():
                continue
            props = dict(r)
            props.pop("id", None)
            rows.append({"id": rid, "props": props})
        neo4j.execute(cypher, {"rows": rows})
        node_count += len(rows)

    # relationships
    rel_count = 0
    for rel_def in relationships:
        if not isinstance(rel_def, dict):
            continue
        rel_type = str(rel_def.get("type") or "").strip()
        from_label = str(rel_def.get("from_node") or "").strip()
        to_label = str(rel_def.get("to_node") or "").strip()
        props = rel_def.get("properties") or []
        if not rel_type or not from_label or not to_label or not isinstance(props, list):
            continue

        pairs: List[Dict[str, str]] = []
        for r in label_records.get(from_label, []):
            from_id = r.get("id")
            if not isinstance(from_id, str) or not from_id.strip():
                continue
            for prop_name in props:
                if not isinstance(prop_name, str):
                    continue
                v = r.get(prop_name)
                if isinstance(v, str) and v.strip():
                    pairs.append({"from_id": from_id, "to_id": v.strip()})
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and item.strip():
                            pairs.append({"from_id": from_id, "to_id": item.strip()})

        if not pairs:
            continue

        cypher = f"""
UNWIND $pairs AS p
MATCH (a:`{from_label}` {{id: p.from_id}})
MATCH (b:`{to_label}` {{id: p.to_id}})
MERGE (a)-[:`{rel_type}`]->(b)
"""
        neo4j.execute(cypher, {"pairs": pairs})
        rel_count += len(pairs)

    return {"nodes_upserted": node_count, "relationships_upserted": rel_count, "wipe": wipe}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Neo4j knowledge graph from K9 ontology YAMLs.")
    parser.add_argument("--wipe", action="store_true", help="Delete all existing nodes/relationships first.")
    args = parser.parse_args()

    settings = APISettings()
    _bootstrap_k9_core(settings)

    if not settings.neo4j_enabled:
        raise SystemExit("Neo4j is not configured. Set K9API_NEO4J_URI, K9API_NEO4J_USERNAME, K9API_NEO4J_PASSWORD.")

    client = Neo4jClient(
        Neo4jConfig(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    )
    try:
        ontology_dir = Path("data/ontology")
        stats = seed_ontology(neo4j=client, ontology_dir=ontology_dir, wipe=bool(args.wipe))
        print(stats)
    finally:
        client.close()


if __name__ == "__main__":
    main()

