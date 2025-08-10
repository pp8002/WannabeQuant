from __future__ import annotations
from pathlib import Path
from typing import Tuple, Set, Dict, Any, List
import json

from .models import Roadmap, Edge

def default_roadmap_path() -> Path:
    # py_app/core/utils.py -> parent je "core", parents[1] je "py_app"
    return Path(__file__).resolve().parent / "data" / "roadmap.json"

def load_roadmap(path: str | Path | None = None) -> Roadmap:
    p = Path(path) if path is not None else default_roadmap_path()

# Pomocné konstrukce hran
# =========================
def _edges_from_prereqs(data: dict) -> Set[Tuple[str, str]]:
        data = json.load(f)

    # lehké migrace pro kompatibilitu
    _ensure_numeric_difficulty(data)
    _ensure_level_numeric(data)
    _ensure_edges(data)

    try:
        return Roadmap(**data)
    except Exception as e:  # hezká hláška s cestou k souboru
        raise ValueError(f"Neplatná struktura dat v {p}: {e}") from e
# =========================
# Pomocné konstrukce hran
# =========================
def _edges_from_prereqs(data: dict) -> Set[Tuple[str, str]]:
    """
    Vytvoří hrany (source -> target) z pole prereqs u každého uzlu.
    Každý prereq 'pre' vede do 'nid' (pre -> nid).
    """
    edges: Set[Tuple[str, str]] = set()
    for n in data.get("nodes", []) or []:
        nid = n.get("id")
        for pre in n.get("prereqs", []) or []:
            if nid and pre:
                edges.add((str(pre), str(nid)))
    return edges


def _edges_from_learning_paths(data: dict) -> Set[Tuple[str, str]]:
    """
    Vytvoří sekvenční hrany z learning_paths.node_sequence.
    Pro každý sousední pár (a, b) v posloupnosti přidá hranu (a -> b).
    """
    edges: Set[Tuple[str, str]] = set()
    for lp in data.get("learning_paths", []) or []:
        seq = lp.get("node_sequence", []) or []
        for i in range(len(seq) - 1):
            a, b = str(seq[i]), str(seq[i + 1])
            edges.add((a, b))
    return edges


# =========================
# Migrace / normalizace
# =========================
def _ensure_numeric_difficulty(data: dict) -> None:
    """
    Migrace: pokud je difficulty string, přemapujeme ho na 1..4.
    Neznámé hodnoty mapujeme na 2 (intermediate).
    """
    mapping = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3,
        "expert": 4,
        # pro jistotu i česky:
        "zacatecnik": 1,
        "stredne pokrocily": 2,
        "pokrocily": 3,
        "expert": 4,
    }
    for n in data.get("nodes", []) or []:
        v = n.get("difficulty")
        if isinstance(v, str):
            n["difficulty"] = mapping.get(v.strip().lower(), 2)


def _ensure_level_numeric(data: dict) -> None:
    """
    Volitelná migrace: pokud 'level' chybí nebo není číslo, nastavíme 1.
    """
    for n in data.get("nodes", []) or []:
        if not isinstance(n.get("level"), int):
            n["level"] = 1


def _ensure_edges(data: dict) -> None:
    """
    Pokud edges chybí, doplníme z prereqs + learning_paths (sjednocená množina).
    Necháváme pouze hrany, jejichž uzly v datasetu existují.
    """
    if "edges" in data and isinstance(data["edges"], list):
        # i tak je lehce pročistíme
        _prune_edges_to_existing_nodes(data)
        return

    e1 = _edges_from_prereqs(data)
    e2 = _edges_from_learning_paths(data)
    merged = sorted(e1 | e2)

    # filtr: pouze hrany, kde oba uzly existují
    existing = {str(n.get("id")) for n in (data.get("nodes") or []) if n.get("id")}
    filtered = [(a, b) for (a, b) in merged if a in existing and b in existing]
    data["edges"] = [{"source": a, "target": b} for (a, b) in filtered]


def _prune_edges_to_existing_nodes(data: dict) -> None:
    """
    Pro jistotu vyhodíme hrany, které odkazují na neexistující uzly.
    """
    nodes_ids = {str(n.get("id")) for n in (data.get("nodes") or []) if n.get("id")}
    new_edges: List[Dict[str, str]] = []
    for e in data.get("edges", []) or []:
        src = str(e.get("source"))
        tgt = str(e.get("target"))
        if src in nodes_ids and tgt in nodes_ids:
            new_edges.append({"source": src, "target": tgt})
    data["edges"] = new_edges


# =========================
# I/O
# =========================
def load_roadmap(path: str | Path) -> Roadmap:
    """
    Načte JSON, provede nenásilnou migraci (difficulty → čísla, doplnění edges,
    zajištění level) a vrátí validní Roadmap (Pydantic v2).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Soubor neexistuje: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    # lehké migrace pro kompatibilitu
    _ensure_numeric_difficulty(data)
    _ensure_level_numeric(data)
    _ensure_edges(data)

    try:
        return Roadmap(**data)
    except Exception as e:  # hezká hláška s cestou k souboru
        raise ValueError(f"Neplatná struktura dat v {p}: {e}") from e


def save_roadmap(roadmap: Roadmap, path: str | Path) -> None:
    """Uloží Roadmap zpět do JSON (hezky formátované)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(roadmap.model_dump(mode="json"), f, ensure_ascii=False, indent=2)


# =========================
# Pomůcky pro UI
# =========================
def category_maps(roadmap: Roadmap):
    """
    Pomocná utilita: vrátí (id→name, id→color, order) pro UI.
    Order je seznam track-id v pořadí, v jakém jsou definovány v JSON.
    """
    id_to_name = {t.id: t.name for t in roadmap.tracks}
    id_to_color = {t.id: (t.color or "#999999") for t in roadmap.tracks}
    order = [t.id for t in roadmap.tracks]
    return id_to_name, id_to_color, order
