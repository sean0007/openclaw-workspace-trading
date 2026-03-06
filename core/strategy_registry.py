"""Minimal strategy registry for discovery and loading of strategy modules.

This scaffold provides a small, testable API that agents and the runtime can
call to list available strategies and import them by module path.
"""
from pathlib import Path
import importlib
import pkgutil
import typing

STRATEGIES_DIR = Path(__file__).resolve().parent.parent / "strategies"


def discover() -> list[dict]:
    """Discover strategy modules under `strategies/`.

    Returns a list of dicts: {"id": module_name, "path": str}
    """
    out = []
    if not STRATEGIES_DIR.exists():
        return out
    # treat strategies as a simple package; list py files
    for p in STRATEGIES_DIR.iterdir():
        if p.is_file() and p.suffix == ".py" and p.name != "__init__.py":
            out.append({"id": p.stem, "path": f"strategies.{p.stem}"})
    return out


def load_strategy(module_path: str):
    """Import and return the module for a strategy by module path.

    Example: `load_strategy('strategies.example_strategy')`
    """
    m = importlib.import_module(module_path)
    return m


def list_ids() -> list[str]:
    return [s["id"] for s in discover()]
