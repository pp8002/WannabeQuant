# ui/layout.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any, Set
import math
import plotly.graph_objects as go
from dash import html, dcc

# ======= Theme =======
BG_COLOR = "#0b1220"
PLOT_BG = "#0b1220"

PATH_COLOR = "#91a4c7"
PATH_WIDTH = 6

NODE_LOCKED = "#3a465f"
NODE_AVAILABLE = "#2dd4bf"
NODE_DONE = "#7ee081"
NODE_CURRENT = "#facc15"
NODE_BORDER = "#0b1220"
NODE_LABEL_COLOR = "#cbd5e1"
BASE_NODE_SIZE = 24

# Ikony
ICON_SIZE_X = 0.9
ICON_SIZE_Y = 0.9
ICON_PATH = "/assets/icons"  # /assets/... Dash servíruje staticky

# ======= helpers: nodes/edges/id =======
def _nodes(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(roadmap.get("nodes", []))

def _idmap(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    return {str(n.get("id", i)): i for i, n in enumerate(nodes)}

def _to_idx(v: Any, idmap: Dict[str, int], n: int) -> Optional[int]:
    if isinstance(v, int):
        return v if 0 <= v < n else None
    if isinstance(v, str) and v.isdigit():
        iv = int(v); return iv if 0 <= iv < n else None
    if isinstance(v, str): return idmap.get(v)
    return None

def _edges(roadmap: Dict[str, Any], idmap: Dict[str, int], n: int) -> List[Tuple[int,int]]:
    raw = roadmap.get("edges", []) or []
    out: List[Tuple[int,int]] = []
    if not raw:
        for j, nd in enumerate(_nodes(roadmap)):
            for pre in nd.get("prereqs", []) or []:
                i = _to_idx(pre, idmap, n)
                if i is not None: out.append((i, j))
        return out
    if isinstance(raw[0], (tuple, list)):
        for a,b in raw:
            i = _to_idx(a, idmap, n); j = _to_idx(b, idmap, n)
            if i is not None and j is not None: out.append((i, j))
        return out
    for e in raw:
        i = _to_idx(e.get("source"), idmap, n); j = _to_idx(e.get("target"), idmap, n)
        if i is not None and j is not None: out.append((i, j))
    return out

# ======= autolayout – Duolingo zig-zag + S-curve backbone =======
def _has_xy(nodes: List[Dict[str, Any]]) -> bool:
    return all(("x" in n and "y" in n) for n in nodes)

def _topo_order(n: int, edges: List[Tuple[int,int]]) -> List[int]:
    indeg = [0]*n; adj=[[] for _ in range(n)]
    for i,j in edges: adj[i].append(j); indeg[j]+=1
    q=[i for i in range(n) if indeg[i]==0]; order=[]; h=0
    while h < len(q):
        u=q[h]; h+=1; order.append(u)
        for v in adj[u]:
            indeg[v]-=1
            if indeg[v]==0: q.append(v)
    if len(order) < n:
        rest=[i for i in range(n) if i not in set(order)]; order+=rest
    return order

def _duo_positions(nodes: List[Dict[str, Any]], edges: List[Tuple[int,int]]) -> List[Tuple[float,float]]:
    n = len(nodes)
    if n == 0: return []
    order = _topo_order(n, edges) if edges else list(range(n))
    X_LEFT, X_RIGHT = -1.25, 1.25
    STEP_Y = -1.45
    WIGGLE = 0.25
    pos = [(0.0, 0.0)] * n
    for k, idx in enumerate(order):
        x = X_LEFT if (k % 2 == 0) else X_RIGHT
        y = k * STEP_Y
        x += 0.12 * math.sin(k*0.7)
        y += WIGGLE * math.sin(k*0.9)
        pos[idx] = (x, y)
    ys = [p[1] for p in pos]; shift = (max(ys) + min(ys)) / 2.0
    pos = [(x, y - shift) for (x, y) in pos]
    return pos

def _nodes_with_xy(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    ns = _nodes(roadmap)
    if not ns: return ns
    if _has_xy(ns):
        return [{**n, "x": float(n["x"]), "y": float(n["y"])} for n in ns]
    idm=_idmap(ns); es=_edges(roadmap, idm, len(ns))
    pos=_duo_positions(ns, es)
    out=[]
    for i,n in enumerate(ns):
        m=dict(n); m["x"],m["y"]=pos[i]; out.append(m)
    return out

# ======= status & barvy =======
def _done_ids(progress: Dict[str, Any]) -> Set[str]:
    p = progress or {}
    done = set()
    tasks = p.get("tasks", {})
    for nid, st in tasks.items():
        if st.get("test_passed") and set(st.get("tasks_done", [])) >= set(st.get("tasks_all", [])):
            done.add(str(nid))
    for nid in p.get("completed", []):
        done.add(str(nid))
    return done

def _node_status(node: Dict[str, Any], done: Set[str]) -> str:
    nid = str(node.get("id"))
    if nid in done: return "done"
    prereqs = [str(p) for p in (node.get("prereqs", []) or [])]
    return "available" if all(p in done for p in prereqs) else "locked"

def _current_id(nodes: List[Dict[str, Any]], done: Set[str]) -> Optional[str]:
    for nd in nodes:
        nid = str(nd.get("id"))
        if _node_status(nd, done) == "available" and nid not in done:
            return nid
    return None

def _axis_ranges(nodes: List[Dict[str, Any]], pad: float = 1.0) -> Tuple[Tuple[float,float], Tuple[float,float]]:
    xs = [float(n["x"]) for n in nodes] or [0.0]
    ys = [float(n["y"]) for n in nodes] or [0.0]
    return ((min(xs)-pad, max(xs)+pad), (min(ys)-pad, max(ys)+pad))

# ======= ikonky (SVG) =======
def _icon_name(node: Dict[str, Any]) -> str:
    nid = str(node.get("id","")).lower()
    lbl = str(node.get("label","")).lower()
    if "python" in nid or "python" in lbl: return "python.svg"
    if "numpy" in nid or "numpy" in lbl: return "numpy.svg"
    if "pandas" in nid or "pandas" in lbl: return "pandas.svg"
    if "plotly" in nid or "plotly" in lbl: return "plotly.svg"
    if "stats" in nid or "stat" in lbl: return "stats.svg"
    if "ml" in nid or "machine" in lbl: return "ml.svg"
    return "book.svg"

def _image_layer(x: float, y: float, filename: str, size_x: float, size_y: float) -> Dict[str, Any]:
    return dict(
        source=f"{ICON_PATH}/{filename}",
        xref="x", yref="y",
        x=x, y=y,
        sizex=size_x, sizey=size_y,
        xanchor="center", yanchor="middle",
        sizing="contain",
        layer="above",
        opacity=1.0,
    )

# ======= Progress ring (oblouk) =======
def _node_progress_ratio(progress: Dict[str, Any], nid: str) -> float:
    st = (progress or {}).get("tasks", {}).get(str(nid), {})
    all_t = st.get("tasks_all", []) or []
    done_t = st.get("tasks_done", []) or []
    base = 0.7 * (len(done_t) / max(1, len(all_t)))  # až 70 % z úkolů
    if st.get("test_passed"):
        base = max(base, 1.0)  # pokud test ok → 100 %
    return float(max(0.0, min(1.0, base)))

def _ring_points(cx: float, cy: float, r: float, frac: float, steps: int = 40) -> Tuple[List[float], List[float]]:
    if frac <= 0: return [], []
    theta = [2*math.pi * frac * (k/steps) for k in range(steps+1)]
    xs = [cx + r * math.cos(t) for t in theta]
    ys = [cy + r * math.sin(t) for t in theta]
    return xs, ys

# ======= Hubs (jemné větvení) =======
def _children(adj: List[List[int]], i: int) -> List[int]:
    return adj[i] if i < len(adj) else []

def _adj_lists(n: int, edges: List[Tuple[int,int]]) -> List[List[int]]:
    adj=[[] for _ in range(n)]
    for i,j in edges: adj[i].append(j)
    return adj

# ======= Figure =======
def make_figure(
    roadmap: Dict[str, Any],
    progress: Optional[Dict[str, Any]] = None,
    center_nid: Optional[str] = None,   # pro "Find" center
    center_zoom: float = 2.6,           # rozsah okna při centru
) -> go.Figure:
    nodes = _nodes_with_xy(roadmap)
    n = len(nodes)
    idmap = _idmap(nodes)
    edges = _edges(roadmap, idmap, n)

    # Backbone path: topo order → S-curve
    order = _topo_order(n, edges) if edges else list(range(n))
    path_x = [nodes[i]["x"] for i in order]
    path_y = [nodes[i]["y"] for i in order]
    path_line = go.Scatter(
        x=path_x, y=path_y, mode="lines",
        line=dict(color=PATH_COLOR, width=PATH_WIDTH),
        hoverinfo="skip", name="Path",
        line_shape="spline",
    )

    # Stavy
    done = _done_ids(progress or {})
    current = _current_id(nodes, done)

    # Progresní overlay (prefix done)
    prefix_k = 0
    for idx in order:
        nid = str(nodes[idx].get("id"))
        if nid in done: prefix_k += 1
        else: break
    progress_line = None
    if prefix_k >= 2:
        px = [nodes[i]["x"] for i in order[:prefix_k]]
        py = [nodes[i]["y"] for i in order[:prefix_k]]
        progress_line = go.Scatter(
            x=px, y=py, mode="lines",
            line=dict(color="#bcd2ff", width=PATH_WIDTH+1),
            hoverinfo="skip", name="Progress",
            line_shape="spline",
        )

    # Hub tečky (uzly s více dětmi)
    adj = _adj_lists(n, edges)
    hub_x, hub_y = [], []
    for i in range(n):
        ch = _children(adj, i)
        if len(ch) >= 2:
            cx, cy = nodes[i]["x"], nodes[i]["y"]
            # směrem k průměru dětí (jen malý posun)
            avgx = sum(nodes[j]["x"] for j in ch) / len(ch)
            avgy = sum(nodes[j]["y"] for j in ch) / len(ch)
            hx = cx + 0.35 * (avgx - cx)
            hy = cy + 0.35 * (avgy - cy)
            hub_x += [hx]; hub_y += [hy]
    hubs_trace = go.Scatter(
        x=hub_x, y=hub_y, mode="markers",
        marker=dict(size=10, color="#263043", line=dict(width=2, color="#44506a")),
        hoverinfo="skip", name="", showlegend=False
    )

    # Barvy/velikosti a hover
    colors=[]; sizes=[]; labels=[]; hovers=[]; coords=[]
    for nd in nodes:
        nid = str(nd.get("id")); lbl = nd.get("label", nid)
        st = _node_status(nd, done)
        labels.append(lbl); coords.append((nd["x"], nd["y"]))
        if st == "done":
            colors.append(NODE_DONE); sizes.append(BASE_NODE_SIZE+6)
        elif nid == current:
            colors.append(NODE_CURRENT); sizes.append(BASE_NODE_SIZE+10)
        elif st == "available":
            colors.append(NODE_AVAILABLE); sizes.append(BASE_NODE_SIZE+2)
        else:
            colors.append(NODE_LOCKED); sizes.append(BASE_NODE_SIZE)
        hovers.append(f"<b>{lbl}</b><br>Status: {st}")

    # Glow pro current
    glow_traces: List[go.Scatter] = []
    if current is not None:
        idxc = next((i for i, nd in enumerate(nodes) if str(nd.get("id")) == current), None)
        if idxc is not None:
            cx, cy = nodes[idxc]["x"], nodes[idxc]["y"]
            for r, op in [(46, 0.25), (34, 0.35), (24, 0.45)]:
                glow_traces.append(go.Scatter(
                    x=[cx], y=[cy], mode="markers",
                    marker=dict(size=r, color=NODE_CURRENT, opacity=op),
                    hoverinfo="skip", showlegend=False, name=""
                ))

    # Základní uzly (kruh + label nahoře)
    nodes_trace = go.Scatter(
        x=[n["x"] for n in nodes], y=[n["y"] for n in nodes],
        mode="markers+text",
        text=[n.get("label","") for n in nodes],
        textposition="top center",
        textfont=dict(color=NODE_LABEL_COLOR, size=12),
        marker=dict(size=sizes, color=colors, line=dict(width=3, color=NODE_BORDER)),
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=hovers, name="Nodes",
    )

    # Progress ringy jako oblouky (kolem každého uzlu)
    rings_x, rings_y = [], []
    ring_sep = []  # None oddělovač
    for nd in nodes:
        nid = str(nd.get("id"))
        r = _node_progress_ratio(progress or {}, nid)
        if r <= 0: continue
        x, y = nd["x"], nd["y"]
        xs, ys = _ring_points(x, y, r=0.72, frac=r, steps=50)
        if xs:
            rings_x += xs + [None]; rings_y += ys + [None]
            ring_sep.append(True)
    rings_trace = go.Scatter(
        x=rings_x, y=rings_y, mode="lines",
        line=dict(color="#e6f0ff", width=6, shape="spline"),
        hoverinfo="skip", name="", showlegend=False
    )

    # SVG ikony a lock overlay
    images = []
    for nd in nodes:
        x, y = nd["x"], nd["y"]
        images.append(_image_layer(x, y, _icon_name(nd), ICON_SIZE_X, ICON_SIZE_Y))
        if _node_status(nd, done) == "locked":
            images.append(_image_layer(x, y, "lock.svg", ICON_SIZE_X, ICON_SIZE_Y))

    # Start here badge (annotation) – pokud existuje current
    annotations = []
    if current is not None:
        idxc = next((i for i, nd in enumerate(nodes) if str(nd.get("id")) == current), None)
        if idxc is not None:
            cx, cy = nodes[idxc]["x"], nodes[idxc]["y"]
            annotations.append(dict(
                x=cx, y=cy - 0.95, xref="x", yref="y",
                text="Start here",
                showarrow=False,
                font=dict(size=12, color="#0b1220", family="Arial Black"),
                align="center",
                bgcolor="#facc15",
                bordercolor="#f59e0b",
                borderwidth=1,
                borderpad=4,
                opacity=0.95,
            ))

    (xr0,xr1),(yr0,yr1)=_axis_ranges(nodes)

    # Pokud máme center_nid → přibliž výhled na daný uzel
    if center_nid is not None:
        try:
            idx = next(i for i, nd in enumerate(nodes) if str(nd.get("id")) == str(center_nid))
            cx, cy = nodes[idx]["x"], nodes[idx]["y"]
            xr0, xr1 = cx - center_zoom, cx + center_zoom
            yr0, yr1 = cy - center_zoom, cy + center_zoom
        except StopIteration:
            pass

    traces = [path_line]
    if progress_line: traces.append(progress_line)
    traces += [hubs_trace, rings_trace, *glow_traces, nodes_trace]

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="none",
        paper_bgcolor=BG_COLOR, plot_bgcolor=PLOT_BG,
        margin=dict(l=16, r=16, t=24, b=16),
        xaxis=dict(range=[xr0, xr1], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[yr0, yr1], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1.0),
        hovermode="closest",
        legend=dict(orientation="h", y=1.02, x=1.0, xanchor="right", font=dict(color="#e2e8f0")),
        images=images,
        annotations=annotations,
        uirevision="static",            # stabilita UI
        transition=dict(duration=0),
    )
    return fig

# ======= Layout stránky =======
def build_layout(fig: go.Figure) -> html.Div:
    return html.Div(
        [
            dcc.Store(id="user-progress", storage_type="local",
                      data={"tasks": {}, "streak_days": 0, "last_day": None}),
            dcc.Store(id="selected-node"),
            dcc.Store(id="last-view", data={"center": None}),  # pro Find/Zoom

            # sticky horní panel
            html.Div(
                [
                    html.Div("WannabeQuant – Roadmap", className="title"),
                    html.Div(
                        [
                            dcc.Input(id="search-node", type="text", placeholder="Find node… (id/label)",
                                      debounce=True, className="search"),
                            html.Button("🔎 Go", id="btn-search", n_clicks=0, className="btn"),
                            html.Button("🗺 Zoom to fit", id="btn-zoom-fit", n_clicks=0, className="btn"),
                            html.Div(id="overall-progress", className="overall-progress"),
                            html.Div(id="streak", className="streak"),
                        ],
                        className="top-right"
                    )
                ],
                className="panel sticky",
            ),

            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="roadmap-graph",
                            figure=fig,
                            config={"displayModeBar": False, "scrollZoom": True, "doubleClick": "reset"},
                            className="graph-card",
                            style={"height": "72vh"},
                        ),
                        className="graph-col",
                    ),
                    html.Div(
                        [
                            html.Div("Milník", className="side-title"),
                            html.Div(id="node-title", className="side-node-title"),
                            html.Div(id="node-prereqs", className="side-prereqs"),
                            html.Div(id="node-status", className="side-status"),
                            html.Div(id="node-links", className="side-links"),
                            html.Hr(),
                            html.Div("Úkoly", className="side-subtitle"),
                            dcc.Checklist(id="tasks-checklist", options=[], value=[], className="tasks"),
                            html.Button("✅ Test splněn / nesplněn", id="btn-test-toggle", n_clicks=0, className="btn success"),
                            html.Div(id="test-status", className="test-status"),
                            html.Hr(),
                            html.Div(
                                [
                                    html.Button("↩ Reset uzlu", id="btn-reset-node", n_clicks=0, className="btn warn"),
                                    html.Button("🧹 Reset všeho", id="btn-reset-all", n_clicks=0, className="btn danger"),
                                ],
                                className="side-actions",
                            ),
                        ],
                        className="side-panel",
                    ),
                ],
                className="two-col",
            ),
        ],
        className="page-wrap",
    )
