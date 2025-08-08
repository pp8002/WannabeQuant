# ui/layout.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
import math
import plotly.graph_objects as go
from dash import html, dcc

# === styl ===
BG_COLOR = "#ffffff"
PLOT_BG = "#ffffff"
GRID = "#eef2f7"

EDGE_COLOR = "#b6c2d9"
EDGE_ACTIVE = "#4f8cff"
NODE_COLOR = "#2dd4bf"
NODE_BORDER = "#0f766e"
NODE_SIZE = 16
NODE_LABEL_COLOR = "#334155"

PROGRESS_MARKER_OUT = "#22c55e"
PROGRESS_MARKER_IN = "#ffffff"

# ---------------------------------------------------------------------
# Pomocné funkce pro ID a bezpečné čtení
# ---------------------------------------------------------------------
def _extract_nodes(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(roadmap.get("nodes", []))

def _id_map(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    m: Dict[str, int] = {}
    for i, n in enumerate(nodes):
        nid = n.get("id", i)
        m[str(nid)] = i
    return m

def _to_idx(v: Any, idmap: Dict[str, int], n_nodes: int) -> Optional[int]:
    if isinstance(v, int):
        return v if 0 <= v < n_nodes else None
    if isinstance(v, str) and v.isdigit():
        iv = int(v)
        return iv if 0 <= iv < n_nodes else None
    if isinstance(v, str):
        return idmap.get(v)
    return None

def _extract_edges(roadmap: Dict[str, Any], idmap: Dict[str, int], n: int) -> List[Tuple[int, int]]:
    """
    Hrany jako (i, j). Podporuje:
      - [(i, j), ...] (mix index/ID)
      - [{"source": i|id, "target": j|id}, ...]
    Nevalidní se přeskočí.
    """
    raw = roadmap.get("edges", []) or []
    out: List[Tuple[int, int]] = []
    if not raw:
        return out

    if isinstance(raw[0], (tuple, list)):
        for e in raw:
            if not isinstance(e, (tuple, list)) or len(e) != 2:
                continue
            i = _to_idx(e[0], idmap, n)
            j = _to_idx(e[1], idmap, n)
            if i is not None and j is not None:
                out.append((i, j))
        return out

    for e in raw:
        s = _to_idx(e.get("source"), idmap, n)
        t = _to_idx(e.get("target"), idmap, n)
        if s is not None and t is not None:
            out.append((s, t))
    return out

# ---------------------------------------------------------------------
# Automatické pozice (když chybí x,y) – topologické vrstvy + jemné vlnění
# ---------------------------------------------------------------------
def _has_xy(nodes: List[Dict[str, Any]]) -> bool:
    return all(("x" in n and "y" in n) for n in nodes)

def _toposort_layers(n: int, edges: List[Tuple[int, int]]) -> List[int]:
    """Vrátí 'úroveň' (hloubku) pro každý uzel (nejdelší vzdál. od zdroje)."""
    indeg = [0]*n
    adj: List[List[int]] = [[] for _ in range(n)]
    for i, j in edges:
        adj[i].append(j)
        indeg[j] += 1
    # Kahn + depth
    q = [i for i in range(n) if indeg[i] == 0]
    depth = [0]*n
    head = 0
    while head < len(q):
        u = q[head]; head += 1
        for v in adj[u]:
            depth[v] = max(depth[v], depth[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return depth

def _compute_positions(nodes: List[Dict[str, Any]], edges: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
    """
    Spočítá pozice pro každý uzel:
      - X = podle vrstvy (hloubky)
      - Y = rozprostřeno + malé vlnění (aby cesta byla 'živá')
    Výsledek je list (x,y) ve stejném pořadí jako nodes.
    """
    n = len(nodes)
    if n == 0:
        return []

    depth = _toposort_layers(n, edges) if edges else list(range(n))
    max_d = max(depth) if depth else 0

    LAYER_GAP_X = 2.0
    LAYER_GAP_Y = 0.9

    # seskup dle vrstvy
    by_layer: Dict[int, List[int]] = {}
    for i, d in enumerate(depth):
        by_layer.setdefault(d, []).append(i)

    pos = [(0.0, 0.0)] * n
    for d, idxs in by_layer.items():
        k = len(idxs)
        if k == 1:
            ys = [0.0]
        else:
            # rovnoměrně rozprostřít kolem 0
            ys = [((j - (k - 1)/2.0) * LAYER_GAP_Y) for j in range(k)]
        # jemné vlnění, aby to nebylo rovné
        for j, i in enumerate(sorted(idxs)):  # zachovej determinismus
            wiggle = 0.25 * math.sin(i * 0.9)
            x = d * LAYER_GAP_X + 0.15 * math.sin(d * 0.7)
            y = ys[j] + wiggle
            pos[i] = (x, y)

    # pokud jsou všechny v jedné vrstvě, udělej stoupající cestu
    if max_d == 0 and n > 1:
        pos = []
        for i in range(n):
            x = i * 1.6
            y = 0.4 * math.sin(i * 0.9)
            pos.append((x, y))

    return pos

def _nodes_with_xy(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vrátí uzly + doplní x,y, pokud chybí (nemutuje originál)."""
    nodes = _extract_nodes(roadmap)
    if not nodes:
        return nodes
    if _has_xy(nodes):
        # zajisti floaty
        out = []
        for n in nodes:
            m = dict(n)
            m["x"] = float(m["x"])
            m["y"] = float(m["y"])
            out.append(m)
        return out

    # spočítej pozice z edges (se string ID i indexy)
    idmap = _id_map(nodes)
    edges = _extract_edges(roadmap, idmap, len(nodes))
    pos = _compute_positions(nodes, edges)
    out = []
    for i, n in enumerate(nodes):
        m = dict(n)
        m["x"], m["y"] = pos[i]
        out.append(m)
    return out

# ---------------------------------------------------------------------
# Další helpery pro vykreslení
# ---------------------------------------------------------------------
def _axis_ranges(nodes: List[Dict[str, Any]], pad: float = 0.8) -> Tuple[Tuple[float,float], Tuple[float,float]]:
    xs = [float(n["x"]) for n in nodes] or [0.0]
    ys = [float(n["y"]) for n in nodes] or [0.0]
    return ((min(xs)-pad, max(xs)+pad), (min(ys)-pad, max(ys)+pad))

def _route_indices(roadmap: Dict[str, Any], route: Optional[List[Any]], idmap: Dict[str, int], n: int) -> List[int]:
    if not route:
        return list(range(n))
    idxs: List[int] = []
    for r in route:
        i = _to_idx(r, idmap, n)
        if i is not None:
            idxs.append(i)
    return idxs if idxs else list(range(n))

def _polyline_points(nodes: List[Dict[str, Any]], idxs: List[int]) -> List[Tuple[float,float]]:
    return [(float(nodes[i]["x"]), float(nodes[i]["y"])) for i in idxs if 0 <= i < len(nodes)]

def _cumlen(pts: List[Tuple[float,float]]) -> List[float]:
    if not pts:
        return [0.0]
    L = [0.0]
    total = 0.0
    for k in range(1, len(pts)):
        dx = pts[k][0] - pts[k-1][0]
        dy = pts[k][1] - pts[k-1][1]
        total += math.hypot(dx, dy)
        L.append(total)
    return L

def _interp_point(pts: List[Tuple[float,float]], L: List[float], t: float) -> Tuple[float,float]:
    if not pts:
        return (0.0, 0.0)
    if len(pts) == 1:
        return pts[0]
    total = L[-1]
    if total <= 1e-9:
        return pts[0]
    s = (t % 1.0) * total
    for i in range(1, len(L)):
        if s <= L[i]:
            s0, s1 = L[i-1], L[i]
            seg = max(s1 - s0, 1e-12)
            a = (s - s0) / seg
            x = pts[i-1][0] + a * (pts[i][0] - pts[i-1][0])
            y = pts[i-1][1] + a * (pts[i][1] - pts[i-1][1])
            return (x, y)
    return pts[-1]

def _progress_polyline(pts: List[Tuple[float,float]], L: List[float], t: float) -> Tuple[List[float], List[float]]:
    if len(pts) <= 1:
        return ([p[0] for p in pts], [p[1] for p in pts])
    total = L[-1]
    if total <= 1e-9:
        return ([p[0] for p in pts], [p[1] for p in pts])
    s = (t % 1.0) * total
    xs, ys = [pts[0][0]], [pts[0][1]]
    for i in range(1, len(pts)):
        if s >= L[i]:
            xs.append(pts[i][0]); ys.append(pts[i][1])
        else:
            s0, s1 = L[i-1], L[i]
            seg = max(s1 - s0, 1e-12)
            a = max(0.0, min(1.0, (s - s0) / seg))
            x = pts[i-1][0] + a * (pts[i][0] - pts[i-1][0])
            y = pts[i-1][1] + a * (pts[i][1] - pts[i-1][1])
            xs.append(x); ys.append(y)
            break
    return xs, ys

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def make_figure(
    roadmap: Dict[str, Any],
    route: Optional[List[Any]] = None,
    t: float = 0.0,
    show_axes: bool = False,
) -> go.Figure:
    # 1) uzly se souřadnicemi (doplníme, pokud chybí)
    nodes = _nodes_with_xy(roadmap)
    n = len(nodes)
    idmap = _id_map(nodes)

    # 2) hrany
    edges = _extract_edges(roadmap, idmap, n)

    # 3) hlavní “cesta” (route) → polyline body
    idxs = _route_indices(roadmap, route, idmap, n)
    pts = _polyline_points(nodes, idxs)
    L = _cumlen(pts)
    px, py = _interp_point(pts, L, t)

    # --- hrany (jemně) ---
    xe, ye = [], []
    for i, j in edges:
        xi, yi = nodes[i]["x"], nodes[i]["y"]
        xj, yj = nodes[j]["x"], nodes[j]["y"]
        xe += [xi, xj, None]; ye += [yi, yj, None]
    edges_trace = go.Scatter(x=xe, y=ye, mode="lines",
                             line=dict(color=EDGE_COLOR, width=2),
                             hoverinfo="skip", name="Path")

    # --- uzly ---
    nx = [n["x"] for n in nodes]
    ny = [n["y"] for n in nodes]
    nlabels = [n.get("label", "") for n in nodes]
    nsize = [int(n.get("size", NODE_SIZE)) for n in nodes]
    ncolor = [n.get("color", NODE_COLOR) for n in nodes]
    nodes_trace = go.Scatter(
        x=nx, y=ny, mode="markers+text",
        text=nlabels, textposition="top center",
        textfont=dict(color=NODE_LABEL_COLOR, size=12),
        marker=dict(size=nsize, color=ncolor, line=dict(width=1, color=NODE_BORDER)),
        hoverinfo="text", name="Nodes",
    )

    # --- zvýrazněná část trasy + aktuální pozice ---
    x_prog, y_prog = _progress_polyline(pts, L, t)
    progress_line = go.Scatter(x=x_prog, y=y_prog, mode="lines",
                               line=dict(color=EDGE_ACTIVE, width=4),
                               hoverinfo="skip", name="Progress")
    progress_outer = go.Scatter(x=[px], y=[py], mode="markers",
                                marker=dict(size=22, color=PROGRESS_MARKER_OUT, opacity=0.9),
                                hoverinfo="skip", name="Here")
    progress_inner = go.Scatter(x=[px], y=[py], mode="markers",
                                marker=dict(size=10, color=PROGRESS_MARKER_IN),
                                hoverinfo="skip", name="", showlegend=False)

    (xr0, xr1), (yr0, yr1) = _axis_ranges(nodes, pad=0.8)
    fig = go.Figure(data=[edges_trace, progress_line, nodes_trace, progress_outer, progress_inner])
    fig.update_layout(
        template="none",
        paper_bgcolor=BG_COLOR, plot_bgcolor=PLOT_BG,
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis=dict(range=[xr0, xr1], showgrid=show_axes, gridcolor=GRID, zeroline=False, visible=show_axes),
        yaxis=dict(range=[yr0, yr1], showgrid=show_axes, gridcolor=GRID, zeroline=False, visible=show_axes,
                   scaleanchor="x", scaleratio=1.0),
        hovermode="closest",
        legend=dict(orientation="h", y=1.02, x=1.0, xanchor="right"),
        transition=dict(duration=250),
    )
    return fig

def build_layout(fig: go.Figure) -> html.Div:
    """Kompatibilní s tvým app.py – bere hotový figure."""
    return html.Div(
        [
            dcc.Store(id="route-store", data={"route": None}),
            dcc.Store(id="anim-state", data={"playing": False, "t": 0.0}),
            html.Div(
                [
                    html.Div("WannabeQuant – Roadmap", className="title"),
                    html.Div(
                        [
                            html.Button("▶ Play", id="btn-play", n_clicks=0, className="btn primary"),
                            html.Button("⏸ Pause", id="btn-pause", n_clicks=0, className="btn"),
                            html.Div(
                                [
                                    html.Label("Speed"),
                                    dcc.Slider(
                                        id="speed-slider", min=0.2, max=3.0, step=0.1, value=1.0,
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                ],
                                className="speed-wrap"
                            ),
                        ],
                        className="controls",
                    ),
                ],
                className="panel",
            ),
            html.Div(
                dcc.Graph(
                    id="roadmap-graph",
                    figure=fig,
                    config={"displayModeBar": True, "scrollZoom": True, "doubleClick": "reset"},
                    className="graph-card",
                ),
                className="graph-wrap",
            ),
            dcc.Interval(id="anim-timer", interval=200, disabled=True),
        ],
        className="page-wrap",
    )
