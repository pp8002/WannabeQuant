from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import math
import plotly.graph_objects as go
from dash import html, dcc

from core.models import Roadmap, Track, Node
from core.utils import category_maps

BG = "rgba(0,0,0,0)"
PLOT_BG = "rgba(0,0,0,0)"

NODE_R = 26
NODE_GLOW = 14
RING_R = 0.54
RING_W = 6

HOVER_BOOST = 4
FOCUS_BOOST = 6
FOCUS_RING = 10

COL_LOCKED = "#3a465f"
COL_AVAIL  = "#22c55e"
COL_DONE   = "#16a34a"
COL_RING   = "#ffffff"

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
    return r, g, b

def _rgba(hex_color: str, a: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    a = max(0.0, min(1.0, float(a)))
    return f"rgba({r},{g},{b},{a})"

def _s_curve_points(n: int, step_y: float = 3.2, amp: float = 2.25):
    pts=[]
    for i in range(n):
        t = i / max(1, n - 1)
        waves = 1.6 if n <= 5 else 2.0
        x = amp * math.sin(t * math.pi * waves)
        y = 0.0 - i * step_y
        pts.append((x,y))
    return pts

def _ring_circle(xc: float, yc: float, r: float = RING_R, steps: int = 120):
    th = [k * (2 * math.pi / steps) for k in range(steps + 1)]
    xs = [xc + r * math.cos(t) for t in th]
    ys = [yc + r * math.sin(t) for t in th]
    return xs, ys

def _status_color(status: str) -> str:
    return COL_DONE if status == "done" else (COL_AVAIL if status == "available" else COL_LOCKED)

def _category_metrics(track: Track, lessons: List[Node]) -> Dict[str, Any]:
    total = len(lessons)
    done = sum(1 for _ in lessons if False)  # TODO: napojíme na progress (zatím 0)
    pct = int(100 * done / max(1, total))
    return {"total": total, "done": done, "pct": pct}

def _category_header(track: Track, lessons: List[Node]) -> html.Div:
    m = _category_metrics(track, lessons)
    return html.Div(
        [
            html.Div(
                [
                    html.Div(track.name, className="tab-title"),
                    html.Div(
                        [
                            html.Div(className="progress-bar-fill", style={"width": f"{m['pct']}%"}),
                            html.Div(f"{m['pct']}%", className="progress-bar-label")
                        ],
                        className="progress-bar"
                    ),
                ],
                className="category-header-left"
            ),
            html.Div(
                [
                    html.Button("▶ Pokračovat", id={"type":"continue-btn","category":track.id}, n_clicks=0, className="btn-continue"),
                    html.Span(id={"type":"cat-meta","category":track.id}, className="cat-meta")
                ],
                className="category-header-right"
            )
        ],
        className="category-header"
    )

def make_category_figure(
    track: Track,
    lessons: List[Node],
    color_hex: str,
    hover_idx: Optional[int] = None,
    focus_idx: Optional[int] = None
) -> go.Figure:
    pts = _s_curve_points(len(lessons))
    items=[]
    for (x,y), node in zip(pts, lessons):
        items.append({
            "x": x, "y": y, "label": node.label, "status": "locked",
            "node_id": node.id, "desc": node.desc or "", "estimate": node.estimate or "",
            "tasks_count": len(node.tasks_all or [])
        })
    if items:
        items[0]["status"] = "available"

    xs=[p["x"] for p in items]; ys=[p["y"] for p in items]
    clr = color_hex or "#8ab4ff"
    glow = _rgba(clr, 0.22); line_glow = _rgba(clr, 0.28)

    traces=[]
    traces.append(go.Scatter(x=xs, y=ys, mode="lines",
        line=dict(color=line_glow, width=22, shape="spline"),
        hoverinfo="skip", showlegend=False))
    traces.append(go.Scatter(x=xs, y=[y-0.20 for y in ys], mode="lines",
        line=dict(color="rgba(0,0,0,0.55)", width=14, shape="spline"),
        hoverinfo="skip", showlegend=False))
    traces.append(go.Scatter(x=xs, y=ys, mode="lines",
        line=dict(color=clr, width=8, shape="spline"),
        hoverinfo="skip", showlegend=False))

    ring_x=[]; ring_y=[]
    for it in items:
        rx, ry = _ring_circle(it["x"], it["y"])
        ring_x += rx + [None]; ring_y += ry + [None]
    traces.append(go.Scatter(x=ring_x, y=ring_y, mode="lines",
        line=dict(color=COL_RING, width=RING_W),
        hoverinfo="skip", showlegend=False))

    halo_sizes=[]
    for i in range(len(items)):
        base = NODE_R + NODE_GLOW
        if i == focus_idx: base += FOCUS_BOOST + 2
        elif i == hover_idx: base += HOVER_BOOST
        halo_sizes.append(base)
    traces.append(go.Scatter(x=xs, y=ys, mode="markers",
        marker=dict(size=halo_sizes, color=glow, line=dict(width=0)),
        hoverinfo="skip", showlegend=False))

    sizes=[]; fill=[]; custom=[]
    for i,it in enumerate(items):
        s = NODE_R + (FOCUS_BOOST if i==focus_idx else HOVER_BOOST if i==hover_idx else 0)
        sizes.append(s); fill.append(_status_color(it["status"]))
        custom.append([it["node_id"], i, it["label"], track.name, it["desc"], it["estimate"], it["tasks_count"]])
    traces.append(go.Scatter(x=xs, y=ys, mode="markers",
        marker=dict(size=sizes, color=fill, line=dict(width=0)),
        hovertemplate="%{customdata[2]}<extra></extra>",
        customdata=custom, showlegend=False))

    if focus_idx is not None and 0 <= focus_idx < len(items):
        fx, fy = xs[focus_idx], ys[focus_idx]
        th=[k*(2*math.pi/140) for k in range(141)]
        ring_fx=[fx + (RING_R+0.22)*math.cos(t) for t in th]
        ring_fy=[fy + (RING_R+0.22)*math.sin(t) for t in th]
        traces.append(go.Scatter(x=ring_fx, y=ring_fy, mode="lines",
            line=dict(color=_rgba("#ffffff",0.85), width=FOCUS_RING),
            hoverinfo="skip", showlegend=False))

    images=[]
    for it in items:
        images.append(dict(source=f"/assets/icons/book.png", xref="x", yref="y",
            x=it["x"], y=it["y"], sizex=0.58, sizey=0.58, xanchor="center", yanchor="middle", layer="above"))

    annotations=[]
    if hover_idx is not None and 0 <= hover_idx < len(items):
        hx,hy = xs[hover_idx], ys[hover_idx]; it = items[hover_idx]
        desc = (it["desc"] or "").strip()
        if len(desc)>120: desc=desc[:117]+"…"
        meta=[]
        if it["estimate"]: meta.append(f"⏱ {it['estimate']}")
        if it["tasks_count"]: meta.append(f"🗂 {it['tasks_count']} témat")
        body=f"<b>{it['label']}</b>"
        if desc: body += f"<br><span style='opacity:.9'>{desc}</span>"
        if meta: body += "<br><span style='opacity:.85'>"+" • ".join(meta)+"</span>"
        annotations.append(dict(
            x=hx+0.35, y=hy+1.15, xref="x", yref="y", align="left",
            text=body, showarrow=False, bgcolor=_rgba(clr,0.92),
            font=dict(color="#fff", size=12),
            bordercolor="rgba(0,0,0,0.25)", borderwidth=1, borderpad=6, opacity=0.96
        ))

    pad=2.8
    xr=(min(xs)-pad, max(xs)+pad) if xs else (-4,4)
    yr=(min(ys)-pad, max(ys)+pad) if ys else (-12,2)

    fig = go.Figure(traces)
    fig.update_layout(
        template="none",
        paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(range=list(xr), showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=list(yr), showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1.0),
        images=images, annotations=annotations, dragmode="pan", uirevision=f"s-curve-{track.id}"
    )
    return fig

def build_layout(roadmap: Roadmap) -> html.Div:
    _, id_to_color, _ = category_maps(roadmap)
    panes=[]
    for tr in roadmap.tracks:
        lessons=[n for n in roadmap.nodes if n.track==tr.id]
        header=_category_header(tr, lessons)
        fig=make_category_figure(tr, lessons, color_hex=(tr.color or id_to_color.get(tr.id, "#8ab4ff")))
        panes.append(
            html.Div(
                [
                    header,
                    dcc.Graph(
                        id={"type":"cat-graph","category":tr.id},
                        figure=fig,
                        config={"displayModeBar": False, "doubleClick": "reset", "scrollZoom": True},
                        className="graph-card", style={"height":"72vh"}
                    ),
                    dcc.Store(id={"type":"cat-state","category":tr.id}, data={"focus": None}),
                    dcc.Store(id={"type":"confetti","category":tr.id}),  # signal pro konfety
                ],
                id={"type":"tab-pane","category":tr.id}, className="tab-pane"
            )
        )

    tabbar = html.Div(
        html.Div([ html.Button("📘", id={"type":"tab-btn","category":tr.id}, n_clicks=0, className="tab-btn", title=tr.name) for tr in roadmap.tracks ],
                 className="tabbar-inner"),
        id="tabbar", className="tabbar"
    )

    default_cat = roadmap.tracks[0].id if roadmap.tracks else "default"
    return html.Div(
        [ dcc.Store(id="active-category", data=default_cat),
          html.Div(panes, id="tabs-container", className="tabs-container"),
          tabbar ],
        className="app-wrap"
    )
