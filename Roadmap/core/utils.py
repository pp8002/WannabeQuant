from __future__ import annotations
from pathlib import Path
from typing import Iterable, Tuple, Set
import json

from .models import Roadmap, Edge


def _edges_from_prereqs(data: dict) -> Set[Tuple[str, str]]:
    """Vytvoří hrany (source -> target) z pole prereqs u každého uzlu."""
    edges: Set[Tuple[str, str]] = set()
    for n in data.get("nodes", []) or []:
        nid = n.get("id")
        for pre in n.get("prereqs", []) or []:
            if nid and pre:
                edges.add((str(pre), str(nid)))
    return edges


def _edges_from_learning_paths(data: dict) -> Set[Tuple[str, str]]:
    """Vytvoří sekvenční hrany z learning_paths.node_sequence."""
    edges: Set[Tuple[str, str]] = set()
    for lp in data.get("learning_paths", []) or []:
        seq = lp.get("node_sequence", []) or []
        for i in range(len(seq) - 1):
            a, b = str(seq[i]), str(seq[i + 1])
            edges.add((a, b))
    return edges


def _ensure_numeric_difficulty(data: dict) -> None:
    """Migrace: pokud je difficulty string, přemapujeme ho na 1..4."""
    mapping = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
    for n in data.get("nodes", []) or []:
        v = n.get("difficulty")
        if isinstance(v, str):
            n["difficulty"] = mapping.get(v.strip().lower(), 2)


def _ensure_edges(data: dict) -> None:
    """Pokud edges chybí, doplníme z prereqs + learning_paths (sjednocená množina)."""
    if "edges" in data and isinstance(data["edges"], list):
        return
    # vytvořit sjednocený set hran
    e1 = _edges_from_prereqs(data)
    e2 = _edges_from_learning_paths(data)
    merged = sorted(e1 | e2)
    data["edges"] = [{"source": a, "target": b} for (a, b) in merged]


def load_roadmap(path: str | Path) -> Roadmap:
    """
    Načte JSON, provede nenásilnou migraci (difficulty → čísla, doplnění edges)
    a vrátí validní Roadmap (Pydantic v2).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Soubor neexistuje: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    # lehké migrace pro kompatibilitu
    _ensure_numeric_difficulty(data)
    _ensure_edges(data)

    try:
        return Roadmap(**data)
    except Exception as e:  # necháme si hezkou chybovou hlášku s cestou
        raise ValueError(f"Neplatná struktura dat v {p}: {e}") from e


def save_roadmap(roadmap: Roadmap, path: str | Path) -> None:
    """Uloží Roadmap zpět do JSON (hezky formátované)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(roadmap.model_dump(mode="json"), f, ensure_ascii=False, indent=2)


def category_maps(roadmap: Roadmap):
    """
    Pomocná utilita: vrátí (id→name, id→color, order) pro UI.
    Order je seznam track-id v pořadí, v jakém jsou definovány v JSON.
    """
    id_to_name = {t.id: t.name for t in roadmap.tracks}
    id_to_color = {t.id: (t.color or "#999999") for t in roadmap.tracks}
    order = [t.id for t in roadmap.tracks]
    return id_to_name, id_to_color, order
