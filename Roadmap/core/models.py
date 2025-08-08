from __future__ import annotations
from typing import List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator

Area = Literal["Programování", "Matematika", "Finance", "Praxe"]

class Node(BaseModel):
    """
    Jeden uzel roadmapy (úkol / kurz / milník).
    """
    id: str
    label: str
    area: Area = "Programování"
    difficulty: Literal[1, 2, 3, 4] = 1
    position: Tuple[float, float, float] = Field(
        (0.0, 0.0, 0.0), description="Pozice v 3D (x, y, z)"
    )
    description: Optional[str] = None
    resources: List[str] = []
    milestone: Optional[str] = None
    prereqs: List[str] = []

    @field_validator("label")
    @classmethod
    def _label_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("label nesmí být prázdný")
        return v

class Edge(BaseModel):
    """
    Hrana z jednoho uzlu do druhého (orientovaná).
    """
    source: str
    target: str

    @model_validator(mode="after")
    def _no_self_loops(self) -> "Edge":
        if self.source == self.target:
            raise ValueError("Edge nesmí mít shodný source a target (self-loop).")
        return self

class Roadmap(BaseModel):
    """
    Celý orientovaný graf roadmapy.
    """
    nodes: List[Node]
    edges: List[Edge]

    @model_validator(mode="after")
    def _validate_graph(self) -> "Roadmap":
        # 1) unikátní ID uzlů
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            # najdi první duplicitní id pro srozumitelnou hlášku
            seen = set()
            dup = next(i for i in ids if (i in seen) or seen.add(i) is None)  # malý trik na zjištění duplikátu
            raise ValueError(f"Duplicate node id: {dup}")

        # 2) všechny hrany musí odkazovat na existující uzly
        node_ids = set(ids)
        for e in self.edges:
            if e.source not in node_ids or e.target not in node_ids:
                raise ValueError(f"Edge odkazuje na neznámý uzel: {e.source} -> {e.target}")

        # 3) (volitelné) zakázat triviální cycles 1-edge (řeší Edge), delší cykly budeme řešit později, pokud budou vadit
        return self

