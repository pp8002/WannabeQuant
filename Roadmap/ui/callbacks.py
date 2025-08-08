# ui/callbacks.py
from __future__ import annotations
from typing import Any, Dict
from dash import Input, Output, State, no_update, ctx
from .layout import make_figure

def register_callbacks(app, roadmap: Dict[str, Any]) -> None:
    def _advance_t(t: float, dt: float) -> float:
        return (t + dt) % 1.0

    @app.callback(
        Output("anim-timer", "disabled"),
        Output("anim-state", "data"),
        Input("btn-play", "n_clicks"),
        Input("btn-pause", "n_clicks"),
        State("anim-state", "data"),
        prevent_initial_call=True,
    )
    def toggle_play(n_play, n_pause, anim_state):
        anim_state = anim_state or {"playing": False, "t": 0.0}
        trig = ctx.triggered_id
        if trig == "btn-play":
            anim_state["playing"] = True
            return False, anim_state   # enable interval
        if trig == "btn-pause":
            anim_state["playing"] = False
            return True, anim_state    # disable interval
        return no_update, no_update

    @app.callback(
        Output("anim-timer", "interval"),
        Input("speed-slider", "value"),
    )
    def set_interval_ms(speed_value):
        base_ms = 200
        v = float(speed_value or 1.0)
        v = max(0.2, min(3.0, v))
        return int(base_ms / v)

    @app.callback(
        Output("roadmap-graph", "figure"),
        Output("anim-state", "data", allow_duplicate=True),  # <- důležité
        Input("anim-timer", "n_intervals"),
        State("anim-state", "data"),
        State("route-store", "data"),
        State("speed-slider", "value"),
        prevent_initial_call=True,
    )
    def tick(_, anim_state, route_store, speed):
        if not anim_state:
            return no_update, no_update

        t = float(anim_state.get("t", 0.0))
        playing = bool(anim_state.get("playing", False))
        route = (route_store or {}).get("route")

        if not playing:
            fig = make_figure(roadmap, route=route, t=t)
            return fig, no_update  # stav se nemění

        v = float(speed or 1.0)
        v = max(0.2, min(3.0, v))
        dt = 0.01 * v
        t = _advance_t(t, dt)
        anim_state = {**anim_state, "t": t}

        fig = make_figure(roadmap, route=route, t=t)
        return fig, anim_state
