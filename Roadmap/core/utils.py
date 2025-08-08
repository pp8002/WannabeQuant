from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import Roadmap

def load_roadmap(path: str | Path) -> Roadmap:
    """
    Načte JSON roadmapy a vrátí validovaný objekt Roadmap (Pydantic).
    - Ošetří existenci souboru
    - Jasné chybové hlášky
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
        # Pydantic vyhodí srozumitelnou chybu (kterou propíšeme dál)
        raise ValueError(f"Neplatná struktura dat v {p}: {e}") from e

