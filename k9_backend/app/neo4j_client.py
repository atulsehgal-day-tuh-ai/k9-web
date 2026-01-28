from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from neo4j import GraphDatabase


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str
    database: str = "neo4j"


class Neo4jClient:
    """
    Thin wrapper around the Neo4j driver.
    - Keeps credentials/config centralized
    - Provides safe helpers for simple query patterns
    """

    def __init__(self, config: Neo4jConfig):
        self._config = config
        self._driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))

    def close(self) -> None:
        self._driver.close()

    def ping(self) -> bool:
        try:
            self.query_one("RETURN 1 AS ok", {})
            return True
        except Exception:
            return False

    def query_one(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        rows = self.query(cypher, params=params, limit=1)
        return rows[0] if rows else None

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        params = params or {}
        with self._driver.session(database=self._config.database) as session:
            result = session.run(cypher, params)
            out: List[Dict[str, Any]] = []
            for i, record in enumerate(result):
                if limit is not None and i >= limit:
                    break
                out.append(record.data())
            return out

    def execute(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> None:
        params = params or {}
        with self._driver.session(database=self._config.database) as session:
            session.run(cypher, params).consume()

