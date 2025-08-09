from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class Metadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None


class Track(BaseModel):
    id: str
    name: str
    color: Optional[str] = None


class Link(BaseModel):
    title: str
    url: str


class Node(BaseModel):
    id: str
    label: str
    track: str                       # odkazuje na Track.id
    level: int = Field(1, ge=1, le=9)
    difficulty: int = Field(1, ge=1, le=4)   # 1..4 (Beginner..Expert)
    desc: Optional[str] = ""
    estimate: Optional[str] = None
    prereqs: List[str] = Field(default_factory=list)
    tasks_all: List[str] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)

    # přijmeme i stringy jako "Beginner", "Intermediate", "Advanced"
    @field_validator("difficulty", mode="before")
    @classmethod
    def _map_difficulty(cls, v):
        if isinstance(v, str):
            m = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
            return m.get(v.strip().lower(), 2)
        return v


class LearningPath(BaseModel):
    name: str
    description: Optional[str] = ""
    node_sequence: List[str] = Field(default_factory=list)


class Edge(BaseModel):
    """Volitelné přímé hrany mezi uzly (source -> target)."""
    source: str
    target: str


class Roadmap(BaseModel):
    metadata: Optional[Metadata] = None
    tracks: List[Track]
    nodes: List[Node]
    learning_paths: List[LearningPath] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)

    # základní konzistence referencí
    @model_validator(mode="after")
    def _validate_refs(self) -> "Roadmap":
        node_ids = {n.id for n in self.nodes}
        track_ids = {t.id for t in self.tracks}

        # validace tracků a prereqů
        for n in self.nodes:
            if n.track not in track_ids:
                raise ValueError(f"Node '{n.id}' odkazuje na neznámý track '{n.track}'.")
            for p in n.prereqs:
                if p not in node_ids:
                    raise ValueError(f"Node '{n.id}' má prereq '{p}', který není v nodes.")

        # validace hran
        for e in self.edges:
            if e.source not in node_ids or e.target not in node_ids:
                raise ValueError(f"Edge '{e.source}->{e.target}' odkazuje na neznámý node.")

        return self
