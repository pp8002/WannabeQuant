from __future__ import annotations
from typing import Dict, Tuple, List
from .models import Roadmap

def serpentine_positions(roadmap: Roadmap, per_col: int = 4, x_step: float = 2.2, y_step: float = 1.8) -> Dict[str, Tuple[float, float]]:
    ids: List[str] = [n.id for n in roadmap.nodes]
    pos: Dict[str, Tuple[float, float]] = {}
    col = 0
    i = 0
    while i < len(ids):
        col_ids = ids[i:i+per_col]
        going_up = (col % 2 == 0)
        y_idx = list(range(len(col_ids))) if going_up else list(reversed(range(len(col_ids))))
        for idx, nid in zip(y_idx, col_ids):
            x = col * x_step
            y = idx * y_step
            pos[nid] = (x, y)
        col += 1
        i += per_col
    return pos

def rounded_edge_points(a: Tuple[float, float], b: Tuple[float, float], k: float = 0.18, n: int = 24):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    nx, ny = -dy, dx
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    cx, cy = mx + k * nx, my + k * ny  # control
    xs, ys = [], []
    for t in [i / (n - 1) for i in range(n)]:
        x = (1 - t)**2 * ax + 2*(1 - t)*t * cx + t**2 * bx
        y = (1 - t)**2 * ay + 2*(1 - t)*t * cy + t**2 * by
        xs.append(x); ys.append(y)
    return xs, ys

def build_route_xy(rm: Roadmap, path_ids: List[str]) -> Tuple[List[float], List[float]]:
    """Z path_ids udělá polyline přes oblouky mezi po sobě jdoucími uzly."""
    pos = serpentine_positions(rm)
    xs_all: List[float] = []; ys_all: List[float] = []
    if len(path_ids) < 2:
        # single point route (stát na místě)
        if path_ids:
            x, y = pos[path_ids[0]]
            xs_all = [x]; ys_all = [y]
        return xs_all, ys_all
    for a, b in zip(path_ids[:-1], path_ids[1:]):
        xa, ya = pos[a]; xb, yb = pos[b]
        xs, ys = rounded_edge_points((xa, ya), (xb, yb))
        if xs_all:
            xs = xs[1:]; ys = ys[1:]  # vyhnout se duplikaci spojů
        xs_all.extend(xs); ys_all.extend(ys)
    return xs_all, ys_all
