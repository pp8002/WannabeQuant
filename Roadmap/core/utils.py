from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
from .models import Roadmap


def load_roadmap(path: str | Path) -> Roadmap:
    """
    Načte JSON roadmapy a vrátí validovaný objekt Roadmap (Pydantic).
    - Ověří existenci souboru
    - Čitelně selže na chybné JSONy
    - Propíše validační chyby (duplicitní ID, neznámé hrany apod.)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Soubor neexistuje: {p.resolve()}")

    try:
        with p.open("r", encoding="utf-8") as f:
            data: Any = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Neplatný JSON v {p}: {e}") from e

    try:
        return Roadmap(**data)
    except Exception as e:
        raise ValueError(f"Neplatná struktura dat v {p}: {e}") from e


def shortest_path(start_id: str, target_id: str, roadmap: Roadmap) -> List[str]:
    """
    Najde nejkratší cestu mezi start_id a target_id v orientovaném grafu pomocí BFS.
    Pokud cesta neexistuje, vrací [].
    """
    # adjacency list
    adj: Dict[str, List[str]] = {}
    for e in roadmap.edges:
        adj.setdefault(e.source, []).append(e.target)

    # BFS
    from collections import deque
    q = deque([start_id])
    prev: Dict[str, str | None] = {start_id: None}

    while q:
        u = q.popleft()
        if u == target_id:
            break
        for v in adj.get(u, []):
            if v not in prev:
                prev[v] = u
                q.append(v)

    if target_id not in prev:
        return []

    # Rekonstrukce cesty
    path: List[str] = []
    cur: str | None = target_id
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return list(reversed(path))
