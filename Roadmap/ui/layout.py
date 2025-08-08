# ui/layout.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any, Set
import math
import plotly.graph_objects as go
from dash import html, dcc

# =========================
# Theme / constants
# =========================
BG_COLOR = "rgba(0,0,0,0)"   # průhledné; animované pozadí řeší CSS
PLOT_BG = "rgba(0,0,0,0)"

PATH_COLOR   = "#96a8cc"
PATH_WIDTH   = 6
BRANCH_WIDTH = 8

NODE_LOCKED    = "#3a465f"
NODE_AVAILABLE = "#2dd4bf"
NODE_DONE      = "#7ee081"
NODE_CURRENT   = "#f59e0b"

BASE_NODE_SIZE = 32

RING_BASE_COLOR     = "#ffffff"
RING_PROGRESS_COLOR = "#7ee081"
RING_BASE_WIDTH     = 12
RING_PROGRESS_WIDTH = 12
RING_RADIUS         = 0.70  # kruh nalepený na „minci“

# Ikony – používáme PNG!
ICON_SIZE_X = 0.9
ICON_SIZE_Y = 0.9
ICON_PATH   = "/assets/icons"
ICON_EXT    = ".png"   # <- důležité

# =========================
# Helpers
# =========================
def _nodes(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(roadmap.get("nodes", []))

def _idmap(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    return {str(n.get("id", i)): i for i, n in enumerate(nodes)}

def _to_idx(v: Any, idmap: Dict[str, int], n: int) -> Optional[int]:
    if isinstance(v, int) and 0 <= v < n: return v
    if isinstance(v, str) and v.isdigit():
        iv = int(v);  return iv if 0 <= iv < n else None
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
        for a, b in raw:
            i = _to_idx(a, idmap, n); j = _to_idx(b, idmap, n)
            if i is not None and j is not None: out.append((i, j))
        return out
    for e in raw:
        i = _to_idx(e.get("source"), idmap, n); j = _to_idx(e.get("target"), idmap, n)
        if i is not None and j is not None: out.append((i, j))
    return out

def _done_ids(progress: Dict[str, Any]) -> Set[str]:
    p=progress or {}
    done=set()
    for nid, st in (p.get("tasks", {}) or {}).items():
        if st.get("test_passed") and set(st.get("tasks_done", [])) >= set(st.get("tasks_all", [])):
            done.add(str(nid))
    for nid in p.get("completed", []): done.add(str(nid))
    return done

def _node_status(node: Dict[str, Any], done: Set[str]) -> str:
    nid=str(node.get("id"))
    if nid in done: return "done"
    prereqs=[str(p) for p in (node.get("prereqs", []) or [])]
    return "available" if all(p in done for p in prereqs) else "locked"

def _current_id(nodes: List[Dict[str, Any]], done: Set[str]) -> Optional[str]:
    # první available, který ještě není done
    for nd in nodes:
        nid=str(nd.get("id"))
        if nid == "quant_core":  # přeskoč střed
            continue
        if _node_status(nd, done)=="available" and nid not in done:
            return nid
    return None

# ------- ikonky -------
def _icon_name(node: Dict[str, Any]) -> str:
    nid=str(node.get("id","")).lower()
    lbl=str(node.get("label","")).lower()
    if any(k in (nid+lbl) for k in ["calc","linear","prob","stat","math"]): return "math"
    if any(k in (nid+lbl) for k in ["python","numpy","pandas","plotly","prog","code"]): return "code"
    if any(k in (nid+lbl) for k in ["ml","ai","model","learn"]): return "ml"
    if any(k in (nid+lbl) for k in ["finance","market","alpha","factor","portfolio","risk"]): return "finance"
    if any(k in (nid+lbl) for k in ["data","sql","pipeline","etl"]): return "data"
    return "book"

def _image_layer(x: float, y: float, filename: str, size_x: float, size_y: float) -> Dict[str, Any]:
    return dict(
        source=f"{ICON_PATH}/{filename}{ICON_EXT}",
        xref="x", yref="y", x=x, y=y,
        sizex=size_x, sizey=size_y,
        xanchor="center", yanchor="middle",
        sizing="contain", layer="above", opacity=1.0,
    )

# ------- progress -------
def _node_progress_ratio(progress: Dict[str, Any], nid: str) -> float:
    st=(progress or {}).get("tasks", {}).get(str(nid), {})
    all_t=st.get("tasks_all", []) or []
    done_t=st.get("tasks_done", []) or []
    base=0.7*(len(done_t)/max(1, len(all_t)))
    if st.get("test_passed"): base=1.0
    return float(max(0.0, min(1.0, base)))

def _ring_points(cx: float, cy: float, r: float, frac: float, steps: int=100):
    if frac <= 0: return [], []
    theta0 = -math.pi/2
    thetas=[theta0 + 2*math.pi*frac*(k/steps) for k in range(steps+1)]
    xs=[cx + r*math.cos(t) for t in thetas]
    ys=[cy + r*math.sin(t) for t in thetas]
    return xs, ys

def _full_ring_points(cx: float, cy: float, r: float, steps: int=160):
    return _ring_points(cx, cy, r, 1.0, steps)

# ------- radiální layout (kmen + větve) -------
def _build_tracks(roadmap: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    tracks: Dict[str, List[Dict[str, Any]]] = {}
    for n in _nodes(roadmap):
        if n.get("id") == "core_quant":  # ignoruj případný center z JSONu
            continue
        track = n.get("track") or n.get("group")
        if not track:
            lbl = (str(n.get("id","")) + " " + str(n.get("label",""))).lower()
            if any(k in lbl for k in ["calc","linear","prob","stat","math"]): track="Matematika"
            elif any(k in lbl for k in ["python","numpy","pandas","plotly","prog","code"]): track="Programování"
            elif any(k in lbl for k in ["ml","model","ai","learn"]): track="ML/Statistika"
            elif any(k in lbl for k in ["risk","portfolio","alpha","factor"]): track="Risk/Portfolio"
            elif any(k in lbl for k in ["data","sql","etl","pipeline"]): track="Data Eng"
            else: track="Finance/Markets"
        tracks.setdefault(track, []).append(n)
    return {k: tracks[k] for k in sorted(tracks.keys())}

def _radial_positions(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    tracks = _build_tracks(roadmap)
    categories = list(tracks.keys())
    m = len(categories)
    if m == 0:  # fallback na prázdno
        return [{"id":"quant_core","label":"Quant","x":0.0,"y":0.0,"__cat__":"CORE","__order__":-1}]
    angles = [(-math.pi/2) + i*(2*math.pi/m) for i in range(m)]
    out_nodes = []
    for t_idx, cat in enumerate(categories):
        angle = angles[t_idx]
        vecx, vecy = math.cos(angle), math.sin(angle)
        branch = tracks[cat]
        for j, n in enumerate(branch):
            r = 1.3 + j * 1.2
            x = r*vecx
            y = r*vecy
            m = dict(n); m["x"], m["y"] = x, y; m["__cat__"]=cat; m["__order__"]=j
            out_nodes.append(m)
    out_nodes.insert(0, {"id":"quant_core","label":"Quant","x":0.0,"y":0.0,"__cat__":"CORE","__order__":-1})
    return out_nodes

def _axis_ranges(nodes: List[Dict[str, Any]], pad: float=1.2):
    xs=[float(n["x"]) for n in nodes] or [0.0]
    ys=[float(n["y"]) for n in nodes] or [0.0]
    return ((min(xs)-pad, max(xs)+pad), (min(ys)-pad, max(ys)+pad))

# =========================
# Figure
# =========================
def make_figure(
    roadmap: Dict[str, Any],
    progress: Optional[Dict[str, Any]] = None,
    center_nid: Optional[str] = None,
    center_zoom: float = 3.2,
    celebrate_nid: Optional[str] = None,
) -> go.Figure:
    nodes = _radial_positions(roadmap)
    done = _done_ids(progress or {})
    current = _current_id(nodes, done)

    # Větve z kmene
    branches: Dict[str, List[Tuple[float,float]]] = {}
    for nd in nodes:
        cat = nd.get("__cat__")
        if cat in ("CORE", None): continue
        branches.setdefault(cat, [(0.0,0.0)])
        branches[cat].append((nd["x"], nd["y"]))

    branch_traces = []
    for pts in branches.values():
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        branch_traces += [
            go.Scatter(x=xs, y=ys, mode="lines",
                       line=dict(color="rgba(145,164,199,0.18)", width=BRANCH_WIDTH+8),
                       hoverinfo="skip", showlegend=False, line_shape="spline"),
            go.Scatter(x=xs, y=ys, mode="lines",
                       line=dict(color=PATH_COLOR, width=BRANCH_WIDTH),
                       hoverinfo="skip", showlegend=False, line_shape="spline"),
        ]

    core_nodes = [nd for nd in nodes if nd["id"] != "quant_core"]

    # Stín pod mincemi
    shadow = go.Scatter(
        x=[nd["x"] for nd in core_nodes],
        y=[nd["y"]-0.10 for nd in core_nodes],
        mode="markers",
        marker=dict(size=[BASE_NODE_SIZE+24]*len(core_nodes),
                    color="rgba(5,10,20,0.6)", line=dict(width=0), opacity=0.35),
        hoverinfo="skip", showlegend=False
    )

    # Bílý prstenec
    base_rx, base_ry = [], []
    for nd in core_nodes:
        xs, ys = _full_ring_points(nd["x"], nd["y"], r=RING_RADIUS, steps=200)
        base_rx += xs + [None]; base_ry += ys + [None]
    ring_base = go.Scatter(x=base_rx, y=base_ry, mode="lines",
                           line=dict(color=RING_BASE_COLOR, width=RING_BASE_WIDTH, shape="spline"),
                           hoverinfo="skip", showlegend=False)

    # Progress prstenec
    prog_rx, prog_ry = [], []
    for nd in core_nodes:
        nid=str(nd.get("id")); frac=_node_progress_ratio(progress or {}, nid)
        if frac <= 0: continue
        xs, ys = _ring_points(nd["x"], nd["y"], r=RING_RADIUS, frac=frac, steps=200)
        prog_rx += xs + [None]; prog_ry += ys + [None]
    ring_prog = go.Scatter(x=prog_rx, y=prog_ry, mode="lines",
                           line=dict(color=RING_PROGRESS_COLOR, width=RING_PROGRESS_WIDTH, shape="spline"),
                           hoverinfo="skip", showlegend=False)

    # „Mince“ — bez textu, jen tooltip
    def _fill_color(nd: Dict[str, Any]) -> str:
        st=_node_status(nd, done)
        if st=="done": return NODE_DONE
        if str(nd.get("id"))==current: return NODE_CURRENT
        if st=="available": return NODE_AVAILABLE
        return NODE_LOCKED

    core = go.Scatter(
        x=[nd["x"] for nd in core_nodes],
        y=[nd["y"] for nd in core_nodes],
        mode="markers",
        marker=dict(size=[BASE_NODE_SIZE]*len(core_nodes),
                    color=[_fill_color(nd) for nd in core_nodes],
                    line=dict(width=0, color="rgba(0,0,0,0)")),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=[f"<b>{nd.get('label', nd.get('id'))}</b><br><span style='color:#9fb4ff'>{nd.get('__cat__')}</span>"
                    for nd in core_nodes],
        showlegend=False
    )

    # Střed („kmen“)
    center = next(nd for nd in nodes if nd["id"]=="quant_core")
    cx, cy = center["x"], center["y"]
    core_center = go.Scatter(x=[cx], y=[cy], mode="markers",
                             marker=dict(size=BASE_NODE_SIZE+8, color="#ffd166", line=dict(width=0)),
                             hoverinfo="skip", showlegend=False)
    trunk_rx, trunk_ry = _full_ring_points(cx, cy, r=0.90, steps=200)
    center_ring = go.Scatter(x=trunk_rx, y=trunk_ry, mode="lines",
                             line=dict(color="#ffffff", width=10, shape="spline"),
                             hoverinfo="skip", showlegend=False)

    # Odlesk
    highlight = go.Scatter(
        x=[nd["x"] - 0.13 for nd in core_nodes],
        y=[nd["y"] + 0.13 for nd in core_nodes],
        mode="markers",
        marker=dict(size=[10]*len(core_nodes), color="rgba(255,255,255,0.28)", line=dict(width=0)),
        hoverinfo="skip", showlegend=False
    )

    # Ikony (PNG)
    images = []
    images.append(_image_layer(cx, cy, "star", 1.0, 1.0))
    for nd in core_nodes:
        images.append(_image_layer(nd["x"], nd["y"], _icon_name(nd), ICON_SIZE_X, ICON_SIZE_Y))
        if _node_status(nd, done)=="locked":
            images.append(_image_layer(nd["x"], nd["y"], "lock", ICON_SIZE_X, ICON_SIZE_Y))

    (xr0,xr1),(yr0,yr1)=_axis_ranges(nodes)

    if center_nid is not None:
        try:
            idx = next(i for i, nd in enumerate(core_nodes) if str(nd.get("id"))==str(center_nid))
            cxx,cyy=core_nodes[idx]["x"], core_nodes[idx]["y"]
            xr0,xr1 = cxx-center_zoom, cxx+center_zoom
            yr0,yr1 = cyy-center_zoom, cyy+center_zoom
        except StopIteration:
            pass

    traces = []
    traces += branch_traces
    traces += [shadow, ring_base, ring_prog, core, highlight, core_center, center_ring]

    fig=go.Figure(data=traces)
    fig.update_layout(
        template="none",
        paper_bgcolor=BG_COLOR, plot_bgcolor=PLOT_BG,
        margin=dict(l=16,r=16,t=24,b=16),
        xaxis=dict(range=[xr0,xr1], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[yr0,yr1], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1.0),
        hovermode="closest",
        showlegend=False,
        images=images,
        uirevision="static",
        transition=dict(duration=0),
    )
    return fig

# =========================
# Page layout (komponenty, které používají callbacky)
# =========================
def build_layout(fig: go.Figure) -> html.Div:
    return html.Div(
        [
            dcc.Store(id="user-progress", storage_type="local",
                      data={"tasks": {}, "streak_days": 0, "last_day": None}),
            dcc.Store(id="selected-node"),
            dcc.Store(id="celebrate"),
            dcc.Store(id="modal-open", data=False),

            html.Div(
                [
                    html.Div("WannabeQuant – Quant Tree", className="title"),
                    html.Div(
                        [
                            dcc.Input(id="search-node", type="text", placeholder="Find node… (id/label)",
                                      debounce=True, className="search"),
                            html.Button("🔎", id="btn-search", n_clicks=0, className="btn"),
                            html.Button("🗺", id="btn-zoom-fit", n_clicks=0, className="btn"),
                            html.Div(id="overall-progress", className="overall-progress"),
                            html.Div(id="streak", className="streak"),
                        ],
                        className="top-right"
                    ),
                ],
                className="panel sticky",
            ),

            html.Div(
                dcc.Graph(
                    id="roadmap-graph",
                    figure=fig,
                    config={"displayModeBar": False, "scrollZoom": True, "doubleClick": "reset"},
                    className="graph-card",
                    style={"height": "78vh"},
                ),
                className="graph-col",
            ),

            # Fullscreen modal (lekce)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(id="modal-title", className="modal-title"),
                            html.Div(id="modal-desc", className="modal-desc"),
                            html.Div(id="modal-links", className="modal-links"),
                            html.Hr(),
                            html.Div("Úkoly", className="side-subtitle"),
                            dcc.Checklist(id="tasks-checklist", options=[], value=[], className="tasks"),
                            html.Div(id="test-status", className="test-status"),
                            html.Div(
                                [
                                    html.Button("✅ Test splněn / nesplněn", id="btn-test-toggle", n_clicks=0, className="btn success"),
                                    html.Button("↩ Reset uzlu", id="btn-reset-node", n_clicks=0, className="btn warn"),
                                    html.Button("🧹 Reset všeho", id="btn-reset-all", n_clicks=0, className="btn danger"),
                                    html.Button("✖ Zavřít", id="btn-close-modal", n_clicks=0, className="btn"),
                                ],
                                className="side-actions",
                            ),
                        ],
                        className="modal-card",
                    ),
                ],
                id="lesson-modal", className="modal-overlay", style={"display": "none"},
            ),
        ],
        className="page-wrap",
    )
