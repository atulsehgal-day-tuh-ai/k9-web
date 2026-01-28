from __future__ import annotations

"""
Minimal smoke checks for the deployed API.

Usage (PowerShell):
  python -m app.smoke_tests --base-url https://<api-host>
"""

import argparse
import json
from typing import Any, Dict

import urllib.request


def _get_json(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url) as resp:  # noqa: S310 (demo smoke test)
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 (demo smoke test)
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Backend base URL, e.g. https://app-k9web-api-demo.azurewebsites.net")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    health = _get_json(f"{base}/health")
    if health.get("ok") is not True:
        raise SystemExit(f"/health failed: {health}")
    print("OK /health")

    # Scenario toggle
    scen = _post_json(f"{base}/api/scenario/critical-monday", {"enabled": True})
    if scen.get("ok") is not True:
        raise SystemExit(f"/api/scenario/critical-monday failed: {scen}")
    print("OK scenario enable")

    scen = _post_json(f"{base}/api/scenario/critical-monday", {"enabled": False})
    if scen.get("ok") is not True:
        raise SystemExit(f"/api/scenario/critical-monday disable failed: {scen}")
    print("OK scenario disable")

    # One deterministic summary call (no LLM needed)
    summary = _get_json(f"{base}/api/summary?window=CURRENT_WEEK")
    if summary.get("ok") is not True:
        raise SystemExit(f"/api/summary failed: {summary}")
    print("OK /api/summary")


if __name__ == "__main__":
    main()

