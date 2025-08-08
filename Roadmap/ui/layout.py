from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from dash import html, dcc
import plotly.graph_objects as go
from core.layout_algo import serpentine_positions, rounded_edge_points

AREA_COLOR = {
    "Programování": "#3b82f6",
    "Matematika":   "#10b981",
    "Finance":      "#f59e0b",
    "Praxe":        "#8b5cf6",
}

def _positions_dict(roadmap: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    class _N: 
        def __init__(self, id): self.id=id
    class _RM:
        def __init__(self, ids): self.nodes=[_N(i) for i in ids]
    rm = _RM([n["id"] for n in roadmap["nodes"]])
    return serpentine_positions(rm, per_col=4)

def make_figure(roadmap: Dict[str, Any], route: Optional[Dict[str, List[float]]] = None, car_idx: int = 0) -> go.Figure:
    nodes: List[Dict[str, Any]] = roadmap["nodes"]
    edges: List[Dict[str, Any]] = roadmap["edges"]
    id_to_pos = _positions_dict(roadmap)

    # hrany (oblouky)
    line_traces = []
    for e in edges:
        a = id_to_pos.get(e["source"]); b = id_to_pos.get(e["target"])
        if not a or not b:
            continue
        xs, ys = rounded_edge_points(a, b, k=0.18, n=24)
        line_traces.append(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=3), hoverinfo="skip", showlegend=False))

    # nody (badge)
    x, y, text, color, size, ids = [], [], [], [], [], []
    for n in nodes:
        px, py = id_to_pos[n["id"]]
        x.append(px); y.append(py)
        ids.append(n["id"])
        label = n.get("label", n["id"])
        area  = n.get("area", "Programování")
        diff  = int(n.get("difficulty", 1))
        text.append(f"{label}<br>{area} • dif {diff}")
        color.append(AREA_COLOR.get(area, "#94a3b8"))
        size.append(26)

    node_trace = go.Scatter(
        x=x, y=y, mode="markers+text",
        marker=dict(size=size, color=color, opacity=0.95, line=dict(color="#ffffff", width=2)),
        text=["●"]*len(x), textposition="middle center",
        hovertext=text, hoverinfo="text",
        customdata=ids, name="Uzly",
    )

    # plánovaná trasa (zvýrazněná)
    route_trace = []
    if route and route.get("x"):
        route_trace = [go.Scatter(x=route["x"], y=route["y"], mode="lines", line=dict(width=5), hoverinfo="skip", name="Trasa")]

    # autíčko (marker na trase)
    car_trace = []
    if route and route.get("x"):
        i = min(max(car_idx, 0), len(route["x"]) - 1)
        car_trace = [go.Scatter(x=[route["x"][i]], y=[route["y"][i]], mode="markers",
                                marker=dict(size=14, symbol="diamond", line=dict(color="#111", width=1)),
                                name="Auto", hoverinfo="skip")]

    fig = go.Figure(data=[*line_traces, node_trace, *route_trace, *car_trace])
    fig.update_layout(
        height=700,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(visible=False, constrain="domain"),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="#ffffff"
    )
    return fig

def build_layout(initial_figure: go.Figure):
    return html.Div(
        [
            # stav
            dcc.Store(id="selection"),
            dcc.Store(id="route"),        # {x:[], y:[]}
            dcc.Store(id="route_idx", data=0),
            dcc.Interval(id="tick", interval=60, disabled=True),  # 60 ms

            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Quant Roadmap (Python/Dash)"),
                            html.P("Klikni na uzel v grafu pro detail. Tlačítkem naplánuj cestu."),
                            dcc.Graph(id="roadmap-2d", figure=initial_figure, style={"height": "70vh"}),
                        ],
                        style={"flex": "2", "padding": "1rem"},
                    ),
                    html.Div(
                        [
                            html.H3("Detail uzlu"),
                            html.Div(id="detail-panel", children="Vyber uzel…"),
                            html.Hr(),
                            html.Div(
                                [
                                    html.Button("Naplánovat cestu sem", id="btn-plan", n_clicks=0, style={"marginRight": "8px"}),
                                    html.Button("Stop", id="btn-stop", n_clicks=0),
                                ]
                            ),
                            html.Div(id="status", style={"marginTop": "0.75rem"}),
                        ],
                        style={"flex": "1", "padding": "1rem", "borderLeft": "1px solid #e5e7eb", "background": "#fafafa", "minWidth": "320px"},
                    ),
                ],
                style={"display": "flex"},
            ),
        ],
        style={"maxWidth": "1100px", "margin": "24px auto", "fontFamily": "system-ui"},
    )
