"""Keel CLI launcher.

The implementation lives in the `app` package; this thin package exists so the
CLI is reachable as `python -m keel` (PATH-independent) in addition to the `keel`
console script installed by `pip install -e .`.
"""
from app.mcp.server import main

__all__ = ["main"]
