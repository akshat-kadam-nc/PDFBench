"""Local usage log for PDF Bench.

Every processed / merged file is appended as one JSON line to a history file in
a per-user data directory. Append-only JSONL keeps writes O(1) (no rewrite of
prior data) and survives app reinstalls, since it lives outside the install dir.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone

_lock = threading.Lock()


def data_dir() -> str:
    """A per-user, writable directory for app data (works when frozen too)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share")
    d = os.path.join(base, "PDFBench")
    os.makedirs(d, exist_ok=True)
    return d


def _path() -> str:
    return os.path.join(data_dir(), "history.jsonl")


def record(entry: dict) -> None:
    """Append one usage record. Never raises into the request path."""
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "id": f"{int(time.time()*1000):x}", **entry}
    try:
        with _lock, open(_path(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — logging must never break processing
        pass


def read(limit: int = 500) -> list[dict]:
    """Most-recent-first list of records (capped at `limit`)."""
    p = _path()
    if not os.path.exists(p):
        return []
    items: list[dict] = []
    try:
        with _lock, open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:  # noqa: BLE001
        return []
    items.reverse()
    return items[:limit]


def stats() -> dict:
    """Totals across the whole log (reads once, cheap for personal volumes)."""
    n = 0
    in_bytes = out_bytes = 0
    for it in read(limit=10**9):
        n += 1
        in_bytes += int(it.get("in_bytes") or 0)
        out_bytes += int(it.get("out_bytes") or 0)
    return {"count": n, "in_bytes": in_bytes, "out_bytes": out_bytes,
            "saved_bytes": max(in_bytes - out_bytes, 0)}


def clear() -> None:
    try:
        with _lock:
            open(_path(), "w").close()
    except Exception:  # noqa: BLE001
        pass
