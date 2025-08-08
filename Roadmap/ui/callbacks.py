from __future__ import annotations
from typing import Dict, Any
from dash import Input, Output, State, no_update, html, ctx  # ctx = kdo spustil callback

from core.utils import shortest_path
from core.layout_algo import build_route_xy


def register_callbacks(app, roadmap: Dict[str, Any]):
    """Zaregistruje všechny callbacky pro 2D Duolingo-like layout."""
    nodes = roadmap["nodes"]
    id_to_node = {n["id"]: n for n in nodes}

    # --- Klik na uzel -> ulož výběr + ukaž detail v pravém panelu ----------------
    @app.callback(
        Output("selection", "data"),
        Output("detail-panel", "children"),
        Input("roadmap-2d", "clickData"),
        prevent_initial_call=True,
    )
    def on_click(clickData):
        if not clickData:
            return no_update, no_update
        pt = clickData["points"][0]
        node_id = pt.get("customdata")
        node = id_to_node.get(node_id)
        if not node:
            return no_update, no_update

        label = node.get("label", node_id)
        area = node.get("area", "Programování")
        diff = node.get("difficulty", 1)
        milestone = node.get("milestone")
        resources = node.get("resources", [])

        detail = html.Div(
            [
                html.H4(label),
                html.P(f"Oblast: {area} • Obtížnost: {diff}"),
                html.P(f"🎯 Milník: {milestone}" if milestone else "—"),
                html.Ul([html.Li(r) for r in resources]) if resources else html.P("Žádné zdroje"),
            ]
        )
        return {"id": node_id}, detail

    # --- Jeden callback pro Plan i Stop (žádné duplicitní Outputs) ---------------
    @app.callback(
        Output("route", "data"),
        Output("status", "children"),
        Input("btn-plan", "n_clicks"),
        Input("btn-stop", "n_clicks"),
        State("selection", "data"),
        prevent_initial_call=True,
    )
    def plan_or_stop(n_plan, n_stop, selection):
        # urči, co spustilo callback
        trig = ctx.triggered_id
        if trig == "btn-stop":
            return None, html.Div("Zastaveno.", style={"color": "#64748b"})

        if trig == "btn-plan":
            if not selection:
                return no_update, html.Div("Nejprve klikni na cíl v grafu.", style={"color": "#ef4444"})
            start = nodes[0]["id"]          # prozatím bereme první uzel jako start
            target = selection["id"]

            # Převeď dict -> Pydantic model (kvůli shortest_path)
            from core.models import Roadmap, Node, Edge
            rm = Roadmap(
                nodes=[
                    Node(**{k: v for k, v in n.items()
                            if k in {"id", "label", "area", "difficulty", "position",
                                     "description", "resources", "milestone", "prereqs"}})
                    for n in nodes
                ],
                edges=[Edge(**e) for e in roadmap["edges"]],
            )

            path_ids = shortest_path(start, target, rm)
            if not path_ids:
                return no_update, html.Div("Cesta nenalezena.", style={"color": "#ef4444"})

            xs, ys = build_route_xy(rm, path_ids)
            return {"x": xs, "y": ys}, html.Div("Plán spuštěn ✓", style={"color": "#16a34a"})

        return no_update, no_update  # fallback

    # --- Interval tick -> posun indexu po polyline (jediný writer route_idx) ----
    @app.callback(
        Output("route_idx", "data"),
        Input("tick", "n_intervals"),
        State("route", "data"),
        State("route_idx", "data"),
        prevent_initial_call=True,
    )
    def on_tick(_, route, idx):
        if not route or not route.get("x"):
            return idx
        cur = idx or 0
        nxt = cur + 1
        if nxt >= len(route["x"]):
            return cur  # konec
        return nxt

    # --- Zapínání/vypínání intervalu (jediný writer tick.disabled) ---------------
    @app.callback(
        Output("tick", "disabled"),
        Input("route", "data"),
        Input("route_idx", "data"),
    )
    def control_interval(route, idx):
        if not route or not route.get("x"):
            return True
        cur = idx or 0
        return cur >= len(route["x"]) - 1

    # --- Repaint grafu podle route a pozice auta ---------------------------------
    @app.callback(
        Output("roadmap-2d", "figure"),
        Input("route", "data"),
        Input("route_idx", "data"),
        prevent_initial_call=False,
    )
    def repaint(route, idx):
        from ui.layout import make_figure  # lazy import
        if not route:
            return make_figure(roadmap)
        return make_figure(roadmap, route=route, car_idx=idx or 0)
