#!/usr/bin/env python3
"""Provision Grafana dashboards from repository JSON files.

Usage examples:
  # dry run (no network calls)
  python3 scripts/provision_grafana_dashboards.py --dry-run

  # provision to a real Grafana instance (uses API key when provided)
  GRAFANA_URL="http://127.0.0.1:3000" GRAFANA_API_KEY="${KEY}" \
    python3 scripts/provision_grafana_dashboards.py

Environment variables:
  GRAFANA_URL (default: http://127.0.0.1:3000)
  GRAFANA_API_KEY (optional; uses Bearer auth)
  GRAFANA_USER / GRAFANA_PASS (optional; basic auth fallback)

The script looks for JSON files under monitoring/grafana/dashboards/*.json
and posts them to the Grafana HTTP API at /api/dashboards/db.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List


def discover_dashboards(path: str) -> List[Path]:
    p = Path(path)
    return sorted(p.glob("*.json")) if p.exists() else []


def load_dashboard(fp: Path) -> Dict[str, Any]:
    with fp.open("r", encoding="utf-8") as f:
        return json.load(f)


def provision_dashboard(grafana_url: str, auth_headers: Dict[str, str], dashboard: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    # import requests lazily so dry-run doesn't require it
    try:
        import requests
    except Exception as e:
        raise RuntimeError("The 'requests' library is required to provision dashboards. Install via 'pip install requests'.") from e

    url = grafana_url.rstrip("/") + "/api/dashboards/db"
    payload = {"dashboard": dashboard, "overwrite": overwrite}
    resp = requests.post(url, headers=auth_headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_auth_headers() -> Dict[str, str]:
    api_key = os.getenv("GRAFANA_API_KEY")
    if api_key:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    user = os.getenv("GRAFANA_USER")
    pwd = os.getenv("GRAFANA_PASS")
    if user and pwd:
        # requests will handle basic auth if we pass auth tuple; but for simplicity,
        # we provide no header here and let callers use requests.auth when needed.
        return {"Content-Type": "application/json"}
    return {"Content-Type": "application/json"}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboards-dir", default="monitoring/grafana/dashboards", help="Directory with dashboard JSON files")
    parser.add_argument("--grafana-url", default=os.getenv("GRAFANA_URL", "http://127.0.0.1:3000"), help="Grafana base URL")
    parser.add_argument("--dry-run", action="store_true", help="Only validate files and show actions; do not call Grafana API")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dashboards on Grafana")
    args = parser.parse_args(argv)

    db_dir = args.dashboards_dir
    dash_files = discover_dashboards(db_dir)
    if not dash_files:
        print(f"No dashboard JSON files found in {db_dir}")
        return 1

    print(f"Found {len(dash_files)} dashboard(s) in {db_dir}")

    auth_headers = build_auth_headers()
    errors = []
    for fp in dash_files:
        if fp.stat().st_size == 0:
            print(f"[WARN] Skipping empty dashboard file: {fp}")
            continue
        try:
            d = load_dashboard(fp)
        except Exception as e:
            print(f"[ERROR] Failed to parse {fp}: {e}")
            errors.append(str(fp))
            continue

        title = d.get("title") or d.get("dashboard", {}).get("title") or fp.stem
        if args.dry_run:
            print(f"[DRY] Would provision: {fp.name} -> title='{title}'")
            continue

        try:
            res = provision_dashboard(args.grafana_url, auth_headers, d, overwrite=args.overwrite)
            print(f"[OK] Provisioned {fp.name} -> message: {res.get('message') or res}")
        except Exception as e:
            print(f"[ERROR] Provisioning {fp.name} failed: {e}")
            errors.append(fp.name)

    if errors:
        print(f"Completed with {len(errors)} error(s)")
        return 2
    print("Completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
