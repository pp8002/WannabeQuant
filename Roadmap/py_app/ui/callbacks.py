from __future__ import annotations
from typing import Dict, Any, List, Optional
from dash import Output, Input, State, MATCH, ALL, no_update, ctx

from py_app.core.models import Roadmap, Track, Node
from py_app.core.utils import category_maps
from py_app.ui.layout import make_category_figure


def _extract_hover_index(hoverData: Optional[Dict[str, Any]]) -> Optional[int]:
    try:
        pts = (hoverData or {}).get("points") or []
        return int(pts[0]["pointIndex"]) if pts else None
    except Exception:
        return None

def _extract_click_index(clickData: Optional[Dict[str, Any]]) -> Optional[int]:
    try:
        pts = (clickData or {}).get("points") or []
        return int(pts[0]["pointIndex"]) if pts else None
    except Exception:
        return None

def register_callbacks(app, roadmap: Roadmap):

    _, id_to_color, _ = category_maps(roadmap)
    track_by_id: Dict[str, Track] = {t.id: t for t in roadmap.tracks}
    lessons_by_track: Dict[str, List[Node]] = {t.id: [n for n in roadmap.nodes if n.track==t.id] for t in roadmap.tracks}

    @app.callback(
        Output("active-category","data"),
        Input({"type":"tab-btn","category":ALL},"n_clicks"),
        prevent_initial_call=True
    )
    def switch_tab(_clicks):
        trg = ctx.triggered_id
        return trg["category"] if trg else no_update

    @app.callback(
        Output({"type":"tab-pane","category":MATCH},"style"),
        Input("active-category","data"),
        State({"type":"tab-pane","category":MATCH},"id"),
    )
    def show_only_active(active_cat, myid):
        return {"display":"block"} if myid["category"]==active_cat else {"display":"none"}

    # klik na uzel -> ulož focus index
    @app.callback(
        Output({"type":"cat-state","category":MATCH},"data"),
        Input({"type":"cat-graph","category":MATCH},"clickData"),
        State({"type":"cat-state","category":MATCH},"data"),
        prevent_initial_call=True
    )
    def store_focus(clickData, cur):
        idx = _extract_click_index(clickData)
        if idx is None: return cur
        cur = (cur or {})
        cur["focus"] = None if cur.get("focus")==idx else idx
        return cur

    # hover/focus -> rebuild
    @app.callback(
        Output({"type":"cat-graph","category":MATCH},"figure"),
        Input("active-category","data"),
        Input({"type":"cat-graph","category":MATCH},"hoverData"),
        Input({"type":"cat-state","category":MATCH},"data"),
        State({"type":"cat-graph","category":MATCH},"id"),
        prevent_initial_call=True
    )
    def rebuild_on_interaction(active_cat, hoverData, cat_state, myid):
        if myid["category"] != active_cat: return no_update
        tr = track_by_id[active_cat]
        lessons = lessons_by_track[active_cat]
        color = tr.color or id_to_color.get(tr.id, "#8ab4ff")
        hover_idx = _extract_hover_index(hoverData)
        focus_idx = (cat_state or {}).get("focus")
        return make_category_figure(tr, lessons, color, hover_idx=hover_idx, focus_idx=focus_idx)

    # přepnutí tabu -> základní figure
    @app.callback(
        Output({"type":"cat-graph","category":MATCH},"figure", allow_duplicate=True),
        Input("active-category","data"),
        State({"type":"cat-graph","category":MATCH},"id"),
        prevent_initial_call=True
    )
    def rebuild_on_tab_switch(active_cat, myid):
        if myid["category"] != active_cat: return no_update
        tr = track_by_id[active_cat]
        lessons = lessons_by_track[active_cat]
        color = tr.color or id_to_color.get(tr.id, "#8ab4ff")
        return make_category_figure(tr, lessons, color)

    # Pokračovat -> fokus na první 'available' (zatím index 0) + konfety signál
    @app.callback(
        Output({"type":"cat-state","category":MATCH},"data", allow_duplicate=True),
        Output({"type":"confetti","category":MATCH},"data", allow_duplicate=True),
        Input({"type":"continue-btn","category":MATCH},"n_clicks"),
        State({"type":"cat-state","category":MATCH},"data"),
        prevent_initial_call=True
    )
    def continue_focus(n_clicks, cur):
        if not n_clicks: return no_update, no_update
        cur = (cur or {})
        cur["focus"] = 0  # TODO: najdi první skutečně dostupný uzel dle progressu
        # pošleme krátký signál do Store -> assets/confetti.js to zachytí
        signal = {"burst": True, "ts": n_clicks}
        return cur, signal

    # metriky kategorie (text vpravo nahoře)
    @app.callback(
        Output({"type":"cat-meta","category":MATCH},"children"),
        Input("active-category","data"),
        State({"type":"cat-meta","category":MATCH},"id"),
    )
    def update_cat_meta(active_cat, myid):
        if myid["category"] != active_cat: return ""
        lessons = lessons_by_track[active_cat]
        return f"{len(lessons)} lekcí"
