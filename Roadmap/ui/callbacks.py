# ui/callbacks.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dash import Input, Output, State, no_update, ctx, html, dcc
from .layout import make_figure
from datetime import datetime
import plotly.graph_objects as go
import urllib.parse as up
import os, glob, re

# =============== Helpers ===============
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

def _done_ids(progress: Dict[str, Any]) -> set:
    return {str(nid) for nid, st in (progress.get("tasks", {}) or {}).items() if st.get("test_passed")}

def _node_by_id(nodes: List[Dict[str, Any]], nid: str) -> Optional[Dict[str, Any]]:
    for n in nodes:
        if str(n.get("id")) == str(nid):
            return n
    return None

def _coerce_tasks_all(nd: Dict[str, Any]) -> List[str]:
    base = nd.get("tasks_all") or nd.get("tasks")
    if isinstance(base, list):
        return [str(x) for x in base]
    return []

def _coerce_desc(nd: Dict[str, Any]) -> str:
    return str(nd.get("desc") or nd.get("description") or "")

def _coerce_estimate(nd: Dict[str, Any]) -> Optional[str]:
    est = nd.get("estimate") or nd.get("time") or nd.get("eta")
    if est:
        s = str(est).strip()
        return s if s else None
    return None

def _coerce_links(nd: Dict[str, Any]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    links = nd.get("links")
    if isinstance(links, list):
        for item in links:
            if isinstance(item, str):
                out.append(("Odkaz", item))
            elif isinstance(item, dict):
                name = str(item.get("name") or item.get("label") or "Odkaz")
                url = str(item.get("url") or "")
                if url:
                    out.append((name, url))
    if nd.get("url"):
        out.append(("📘 Lekce", str(nd["url"])))
    if nd.get("test_url"):
        out.append(("🧪 Test", str(nd["test_url"])))
    # dedupe
    seen = set(); uniq=[]
    for name, url in out:
        key=(name,url)
        if key in seen: continue
        seen.add(key); uniq.append((name,url))
    return uniq

def _progress_ratio_from_state(node_state: Dict[str, Any]) -> float:
    all_t = node_state.get("tasks_all", []) or []
    done_t = node_state.get("tasks_done", []) or []
    base = 0.7 * (len(done_t) / max(1, len(all_t)))
    if node_state.get("test_passed"):
        base = 1.0
    return max(0.0, min(1.0, float(base)))

# --- Terraria donut progress (emerald on dark track, cream label) ---
def _progress_figure(ratio: float) -> go.Figure:
    pct = max(0, min(100, int(round(ratio * 100))))
    fg = "#4ADE80"   # emerald
    bg = "#0E2428"   # dark teal track
    txt = "#FFE8C2"  # cream label (ladí s ringy)
    fig = go.Figure(
        data=[
            go.Pie(
                values=[pct, max(0, 100 - pct)],
                hole=0.75,
                sort=False,
                direction="clockwise",
                rotation=90,              # začni nahoře (jako ringy)
                textinfo="none",
                hoverinfo="skip",
                marker=dict(colors=[fg, bg], line=dict(width=0))
            )
        ]
    )
    label = f"{pct}%"
    if pct == 100:
        label = "100% ✨"
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(text=label, x=0.5, y=0.5, xanchor="center", yanchor="middle",
                          showarrow=False, font=dict(size=18, color=txt))],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# Markdown loader (assets/lessons/<id>/<nn>-*.md)
def _find_md_file(node_id: str, index: int) -> Optional[str]:
    folder = os.path.join("assets", "lessons", node_id)
    patt = os.path.join(folder, f"{index:02d}-*.md")
    matches = glob.glob(patt)
    if matches:
        return matches[0]
    return None

def _read_md(path: str) -> Tuple[Optional[str], Optional[str], str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
    except Exception:
        return None, None, "_Obsah bude doplněn._"

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", txt, re.S)
    title = None
    meta = None
    body = txt
    if m:
        meta_block = m.group(1)
        body = m.group(2)
        mt = re.search(r"^title:\s*(.+)$", meta_block, re.M)
        me = re.search(r"^estimate:\s*(.+)$", meta_block, re.M)
        title = mt.group(1).strip() if mt else None
        if me:
            meta = f"⏱ {me.group(1).strip()}"
    return title, meta, body

# =============== Callbacks ===============
def register_callbacks(app, roadmap: Dict[str, Any]) -> None:
    nodes = roadmap.get("nodes", [])

    # Router: home/lesson
    @app.callback(
        Output("home-page", "style"),
        Output("lesson-page", "style"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def switch_pages(pathname):
        if pathname and pathname.startswith("/lesson"):
            return {"display": "none"}, {"display": "block"}
        return {"display": "block"}, {"display": "none"}

    # Klik v grafu → pokud uzel zamčený, ukaž tooltip; jinak otevři modal
    @app.callback(
        Output("selected-node", "data"),
        Output("modal-open", "data"),
        Output("lock-toast-text", "children"),
        Output("lock-toast", "style"),
        Input("roadmap-graph", "clickData"),
        State("user-progress", "data"),
        prevent_initial_call=True,
    )
    def select_node(clickData, progress):
        if not clickData:
            return no_update, no_update, no_update, no_update
        pt = clickData["points"][0]
        if "customdata" not in pt or not isinstance(pt["customdata"], (list, tuple)) or len(pt["customdata"]) < 1:
            return no_update, no_update, no_update, no_update

        nid = str(pt["customdata"][0])
        nd = _node_by_id(nodes, nid)
        if not nd:
            return no_update, no_update, no_update, no_update

        progress = _normalize_progress(progress)
        done_ids = _done_ids(progress)
        # zkontroluj prereqs
        missing = [pid for pid in (nd.get("prereqs") or []) if str(pid) not in done_ids]
        if missing:
            names = []
            for mid in missing:
                n2 = _node_by_id(nodes, str(mid))
                names.append(n2.get("label", str(mid)) if n2 else str(mid))
            msg = "🔒 Nejdřív dokonči: " + ", ".join(names)
            return no_update, False, msg, {"display": "flex"}

        # odemčeno → otevři modal
        return {"id": nid}, True, "", {"display": "none"}

    # Zavři toast
    @app.callback(
        Output("lock-toast", "style", allow_duplicate=True),
        Input("lock-toast-close", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_toast(n):
        return {"display": "none"}

    # Vyhledávání & zoom
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
        Output("modal-estimate", "children"),
        Output("topics-list", "children"),
        Output("test-status", "children"),
        Output("lesson-modal", "style"),
        Output("modal-progress", "figure"),
        Input("selected-node", "data"),
        State("user-progress", "data"),
        State("modal-open", "data"),
    )
    def populate_modal(selected, progress, is_open):
        progress = _normalize_progress(progress)
        if not selected or not is_open:
            return "", "", "", "", [], "", {"display": "none"}, go.Figure()
        nid = str(selected.get("id"))
        nd = _node_by_id(nodes, nid)
        if not nd:
            return "", "", "", "", [], "", {"display": "none"}, go.Figure()

        tasks_all = _coerce_tasks_all(nd)
        node_state = progress["tasks"].get(
            nid,
            {"tasks_all": tasks_all, "tasks_done": [], "test_passed": False}
        )
        node_state.setdefault("tasks_all", tasks_all)
        node_state.setdefault("tasks_done", [])
        node_state.setdefault("test_passed", False)

        title = nd.get("label", nid)
        desc  = _coerce_desc(nd) or " "
        links_pairs = _coerce_links(nd)
        links_children = [html.A(name, href=url, target="_blank", rel="noopener", className="link") for (name, url) in links_pairs]
        links_div = html.Div(links_children, className="links") if links_children else ""

        estimate = _coerce_estimate(nd)
        estimate_div = html.Div(f"⏱ {estimate}", className="modal-estimate") if estimate else ""

        topics_children = [
            html.Li(
                html.A(topic, href=f"/lesson?id={nid}&t={i}", className="topic-link"),
                className="topic-item"
            )
            for i, topic in enumerate(tasks_all, start=1)
        ]

        ratio = _progress_ratio_from_state(node_state)
        prog_fig = _progress_figure(ratio)
        test_text = f"Test: {'✔ splněn' if node_state['test_passed'] else '✖ nesplněn'}"

        return (
            title, desc, links_div, estimate_div,
            topics_children, test_text, {"display": "flex"}, prog_fig
        )

    # Zavření modalu (funguje, pokud v layoutu existuje tlačítko s id="btn-close-modal")
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
        prevent_initial_call=True,
    )
    def refresh_fig(progress):
        progress = _normalize_progress(progress)
        fig = make_figure(roadmap, progress)
        ns = roadmap.get("nodes", [])
        total = len(ns) if ns else 1
        done_ids = _done_ids(progress)
        pct = int(round(100*len(done_ids)/max(total,1)))
        overall = f"Progress: {pct}% ({len(done_ids)}/{total})"
        streak = f"🔥 Streak: {int(progress.get('streak_days', 0))} dní"
        return fig, overall, streak

    # === LESSON VIEWER ===
    @app.callback(
        Output("lesson-title", "children"),
        Output("lesson-meta", "children"),
        Output("lesson-md", "children"),
        Output("lesson-prev", "href"),
        Output("lesson-next", "href"),
        Input("url", "pathname"),
        Input("url", "search"),
        prevent_initial_call=False,
    )
    def lesson_loader(pathname, search):
        if not pathname or not pathname.startswith("/lesson"):
            return no_update, no_update, no_update, no_update, no_update

        qs = up.parse_qs((search or "").lstrip("?"))
        node_id = (qs.get("id", [""])[0] or "").strip()
        try:
            topic_idx = int((qs.get("t", ["1"])[0] or "1"))
        except ValueError:
            topic_idx = 1

        nd = _node_by_id(nodes, node_id) if node_id else None
        if not nd:
            return "Lekce", "", "_Tato lekce neexistuje._", "/", "/"

        tasks_all = _coerce_tasks_all(nd)
        n_topics = max(1, len(tasks_all))
        topic_idx = max(1, min(topic_idx, n_topics))

        md_path = _find_md_file(node_id, topic_idx)
        if not md_path:
            title = f"{nd.get('label','')}: {tasks_all[topic_idx-1] if tasks_all else f'Téma {topic_idx}'}"
            meta = f"⏱ {nd.get('estimate','')}" if nd.get("estimate") else ""
            body = "_Obsah bude doplněn. Vložte soubor:_  \n"
            body += f"`assets/lessons/{node_id}/{topic_idx:02d}-your-topic.md`"
        else:
            fm_title, fm_meta, body = _read_md(md_path)
            title = fm_title or f"{nd.get('label','')}: {tasks_all[topic_idx-1] if tasks_all else f'Téma {topic_idx}'}"
            meta = fm_meta or (f"⏱ {nd.get('estimate','')}" if nd.get("estimate") else "")

        prev_href = f"/lesson?id={node_id}&t={topic_idx-1}" if topic_idx > 1 else f"/lesson?id={node_id}&t=1"
        next_href = f"/lesson?id={node_id}&t={topic_idx+1}" if topic_idx < n_topics else f"/lesson?id={node_id}&t={n_topics}"

        return title, meta, body, prev_href, next_href

    # Tlačítko „Označit lekci jako hotovou“ → uloží test_passed=True pro uzel
    @app.callback(
        Output("user-progress", "data"),
        Output("roadmap-graph", "figure", allow_duplicate=True),
        Input("btn-complete-lesson", "n_clicks"),
        State("user-progress", "data"),
        State("url", "search"),
        prevent_initial_call=True,
    )
    def complete_lesson(n, progress, search):
        progress = _normalize_progress(progress)
        qs = up.parse_qs((search or "").lstrip("?"))
        node_id = (qs.get("id", [""])[0] or "").strip()
        if not node_id:
            return progress, no_update
        node_state = progress["tasks"].get(node_id, {"tasks_all": [], "tasks_done": [] , "test_passed": False})
        node_state["test_passed"] = True
        progress["tasks"][node_id] = node_state
        fig = make_figure(roadmap, progress)
        return progress, fig
