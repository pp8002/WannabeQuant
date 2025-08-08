# ui/callbacks.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dash import Input, Output, State, no_update, ctx, html
from .layout import make_figure
from datetime import datetime

def _today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def _normalize_progress(progress: Any) -> Dict[str, Any]:
    if not isinstance(progress, dict):
        return {"tasks": {}, "streak_days": 0, "last_day": None}
    progress.setdefault("tasks", {})
    progress.setdefault("streak_days", 0)
    progress.setdefault("last_day", None)
    if not isinstance(progress["tasks"], dict):
        progress["tasks"] = {}
    fixed = {}
    for nid, st in progress["tasks"].items():
        if isinstance(st, dict):
            st.setdefault("tasks_all", [])
            st.setdefault("tasks_done", [])
            st.setdefault("test_passed", False)
            fixed[str(nid)] = st
        else:
            fixed[str(nid)] = {"tasks_all": [], "tasks_done": [], "test_passed": bool(st)}
    progress["tasks"] = fixed
    return progress

def register_callbacks(app, roadmap: Dict[str, Any]) -> None:
    nodes = roadmap.get("nodes", [])

    def _node(nid: str) -> Optional[Dict[str, Any]]:
        for n in nodes:
            if str(n.get("id")) == str(nid):
                return n
        return None

    def _default_tasks(nd: Dict[str, Any]) -> List[str]:
        base = nd.get("tasks")
        if isinstance(base, list) and base:
            return [str(x) for x in base]
        return ["Teorie", "Cvičení", "Mini-projekt"]

    # klik do grafu → vyber uzel + otevři modal
    @app.callback(
        Output("selected-node", "data"),
        Output("modal-open", "data"),
        Input("roadmap-graph", "clickData"),
        prevent_initial_call=True,
    )
    def select_node(clickData):
        if not clickData:
            return no_update, no_update
        pt = clickData["points"][0]
        x, y = float(pt["x"]), float(pt["y"])
        best, bestd = None, 1e9
        for nd in nodes:
            xx = float(nd.get("x", 0.0)); yy = float(nd.get("y", 0.0))
            d = (xx-x)**2 + (yy-y)**2
            if d < bestd:
                bestd, best = d, nd
        return ({"id": best.get("id")} if best else no_update, True)

    # Find & Zoom
    @app.callback(
        Output("selected-node", "data", allow_duplicate=True),
        Output("roadmap-graph", "figure", allow_duplicate=True),
        Input("btn-search", "n_clicks"),
        Input("btn-zoom-fit", "n_clicks"),
        State("search-node", "value"),
        State("user-progress", "data"),
        prevent_initial_call=True,
    )
    def find_and_zoom(n_search, n_fit, query, progress):
        progress = _normalize_progress(progress)
        trig = ctx.triggered_id
        if trig == "btn-zoom-fit":
            fig = make_figure(roadmap, progress, center_nid=None)
            return no_update, fig
        if trig == "btn-search":
            if not query:
                return no_update, no_update
            q = str(query).strip().lower()
            for n in nodes:
                nid = str(n.get("id","")).lower()
                lbl = str(n.get("label","")).lower()
                if q == nid or q in lbl or q in nid:
                    fig = make_figure(roadmap, progress, center_nid=str(n.get("id")))
                    return {"id": n.get("id")}, fig
        return no_update, no_update

    # Naplnění modalu
    @app.callback(
        Output("modal-title", "children"),
        Output("modal-desc", "children"),
        Output("modal-links", "children"),
        Output("tasks-checklist", "options"),
        Output("tasks-checklist", "value"),
        Output("test-status", "children"),
        Output("lesson-modal", "style"),
        Input("selected-node", "data"),
        State("user-progress", "data"),
        State("modal-open", "data"),
    )
    def populate_modal(selected, progress, is_open):
        progress = _normalize_progress(progress)
        if not selected or not is_open:
            return "", "", "", [], [], "", {"display": "none"}
        nid = str(selected.get("id"))
        nd = _node(nid)
        if not nd:
            return "", "", "", [], [], "", {"display": "none"}

        tasks_all = _default_tasks(nd)
        node_state = progress["tasks"].get(nid, {"tasks_all": tasks_all, "tasks_done": [], "test_passed": False})
        tasks_done = node_state.get("tasks_done", [])
        test_passed = bool(node_state.get("test_passed", False))

        title = nd.get("label", nid)
        desc = nd.get("description", " ")
        links = []
        if nd.get("url"):
            links.append(html.A("📘 Lekce", href=str(nd["url"]), target="_blank", className="link"))
        if nd.get("test_url"):
            links.append(html.A("🧪 Test", href=str(nd["test_url"]), target="_blank", className="link"))
        links_div = html.Div(links, className="links") if links else ""

        return (
            title, desc, links_div,
            [{"label": t, "value": t} for t in tasks_all],
            tasks_done,
            f"Test: {'✔ splněn' if test_passed else '✖ nesplněn'}",
            {"display": "flex"},
        )

    # Uložení checklistu
    @app.callback(
        Output("user-progress", "data", allow_duplicate=True),
        Input("tasks-checklist", "value"),
        State("tasks-checklist", "options"),
        State("selected-node", "data"),
        State("user-progress", "data"),
        prevent_initial_call=True,
    )
    def save_tasks(value, options, selected, progress):
        if not selected:
            return no_update
        progress = _normalize_progress(progress)
        nid = str(selected.get("id"))
        tasks_all = [opt["value"] for opt in (options or [])]
        node_state = progress["tasks"].get(nid, {"tasks_all": tasks_all, "tasks_done": [], "test_passed": False})
        node_state["tasks_all"] = tasks_all
        node_state["tasks_done"] = list(value or [])
        today = _today_key()
        if progress.get("last_day") != today:
            progress["streak_days"] = int(progress.get("streak_days", 0)) + 1
            progress["last_day"] = today
        progress["tasks"][nid] = node_state
        return progress

    # Test toggle / reset
    @app.callback(
        Output("user-progress", "data", allow_duplicate=True),
        Output("tasks-checklist", "value", allow_duplicate=True),
        Output("test-status", "children", allow_duplicate=True),
        Output("roadmap-graph", "figure", allow_duplicate=True),
        Output("celebrate", "data", allow_duplicate=True),
        Input("btn-test-toggle", "n_clicks"),
        Input("btn-reset-node", "n_clicks"),
        Input("btn-reset-all", "n_clicks"),
        State("selected-node", "data"),
        State("tasks-checklist", "options"),
        State("user-progress", "data"),
        prevent_initial_call=True,
    )
    def actions(n_test, n_reset_node, n_reset_all, selected, options, progress):
        trig = ctx.triggered_id
        progress = _normalize_progress(progress)

        if trig == "btn-reset-all":
            newp = {"tasks": {}, "streak_days": 0, "last_day": None}
            fig = make_figure(roadmap, newp)
            return newp, [], "Test: ✖ nesplněn", fig, None

        if not selected:
            return no_update, no_update, no_update, no_update, no_update

        nid = str(selected.get("id"))
        tasks_all = [opt["value"] for opt in (options or [])]
        node_state = progress["tasks"].get(nid, {"tasks_all": tasks_all, "tasks_done": [], "test_passed": False})

        if trig == "btn-reset-node":
            progress["tasks"][nid] = {"tasks_all": tasks_all, "tasks_done": [], "test_passed": False}
            fig = make_figure(roadmap, progress)
            return progress, [], "Test: ✖ nesplněn", fig, None

        celebrate = None
        if trig == "btn-test-toggle":
            node_state.setdefault("tasks_all", tasks_all)
            node_state.setdefault("tasks_done", [])
            was_done = bool(node_state.get("test_passed", False)) and set(node_state.get("tasks_done", [])) >= set(node_state.get("tasks_all", []))
            node_state["test_passed"] = not bool(node_state.get("test_passed", False))
            progress["tasks"][nid] = node_state
            now_done = bool(node_state.get("test_passed", False)) and set(node_state.get("tasks_done", [])) >= set(node_state.get("tasks_all", []))
            if (not was_done) and now_done:
                celebrate = nid
            fig = make_figure(roadmap, progress, celebrate_nid=celebrate)
            return progress, node_state["tasks_done"], f"Test: {'✔ splněn' if node_state['test_passed'] else '✖ nesplněn'}", fig, celebrate

        return no_update, no_update, no_update, no_update, no_update

    # Zavření modalu
    @app.callback(
        Output("lesson-modal", "style", allow_duplicate=True),
        Output("modal-open", "data", allow_duplicate=True),
        Input("btn-close-modal", "n_clicks"),
        State("lesson-modal", "style"),
        prevent_initial_call=True,
    )
    def close_modal(n, style):
        return {"display": "none"}, False

    # Redraw & metriky
    @app.callback(
        Output("roadmap-graph", "figure"),
        Output("overall-progress", "children"),
        Output("streak", "children"),
        Input("user-progress", "data"),
        State("celebrate", "data"),
        prevent_initial_call=True,
    )
    def refresh_fig(progress, celebrate):
        progress = _normalize_progress(progress)
        fig = make_figure(roadmap, progress, celebrate_nid=celebrate)
        ns = roadmap.get("nodes", [])
        total = len(ns) if ns else 1
        done_ids = set()
        for nid, st in progress["tasks"].items():
            if st.get("test_passed") and set(st.get("tasks_done", [])) >= set(st.get("tasks_all", [])):
                done_ids.add(nid)
        pct = int(round(100*len(done_ids)/max(total,1)))
        overall = f"Progress: {pct}% ({len(done_ids)}/{total})"
        streak = f"🔥 Streak: {int(progress.get('streak_days', 0))} dní"
        return fig, overall, streak
