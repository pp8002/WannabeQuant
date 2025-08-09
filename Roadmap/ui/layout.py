# ui/layout.py
# ======================================================================================
# Kompletní layout pro interaktivní roadmapu (Dash + Plotly) s 4 kategoriemi.
# - zachovává původní vizuální styl (koncentrické kružnice, uzly, ikonky, prstence),
# - přesné umístění štítků kategorií (začátek/konec větve po tečně),
# - volitelně podkladové poloprůhledné sektory pod větvemi (půlkruhy / výseče),
# - barvy kategorií se načítají z roadmap["tracks"]; pokud chybí, použijí se fallbacky.
#
# Poznámky:
#  - Funkce make_figure(roadmap, ...) očekává dict podle nového JSON (se 4 tracks).
#  - build_layout(fig) vrací Dash stránku s routerem (home/lesson) jako dřív.
#  - Bezpečně pracujeme s fig.layout.shapes a fig.layout.annotations (list vs tuple).
#  - Všechny pomocné funkce jsou v tomto souboru – drop-in náhrada.
# ======================================================================================

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any, Set, Iterable
import math
import plotly.graph_objects as go
from dash import html, dcc

# ======================================================================================
# VZHLED / KONSTANTY
# ======================================================================================

# Pozadí grafu necháváme transparentní – tvůj Terraria obrázek v CSS zůstane vidět
BG_COLOR = "rgba(0,0,0,0)"
PLOT_BG  = "rgba(0,0,0,0)"

# Větve – barva samotných větví (nikoli kategorií) – použijeme paletu, ale reálně
# barvu větve řeší barevný podklad/štítek kategorie. Tohle je „stroke“ větví.
BRANCH_WIDTH  = 7
BRANCH_COLORS = [
    "#8FB3FF", "#7EE081", "#F8C16A", "#9AE6B4", "#FBB6CE",
    "#A3BFFA", "#B9FBC0", "#FFD6A5", "#CDB4DB", "#90DBF4"
]

# Uzly – stavy a velikosti
BASE_NODE_SIZE = 26
NODE_LOCKED    = "#3a465f"
NODE_AVAILABLE = "#2dd4bf"
NODE_DONE      = "#7ee081"
NODE_CURRENT   = "#f59e0b"

# Prstence kolem uzlů – základ + progress
RING_BASE_COLOR     = "#ffffff"
RING_PROGRESS_COLOR = "#7ee081"
RING_BASE_WIDTH     = 10
RING_PROGRESS_WIDTH = 10
RING_RADIUS         = 0.62

# Ikony
ICON_PATH   = "/assets/icons"
ICON_EXT    = ".png"
ICON_SIZE_X = 0.62
ICON_SIZE_Y = 0.62

# Kategorie – fallback barvy pro 4 hlavní tratě (když nejsou v roadmap["tracks"])
FALLBACK_CATEGORY_COLORS = {
    "math-fundamentals":        "#1f77b4",  # modrá
    "programming":              "#2ca02c",  # zelená
    "finance-theory":           "#ff7f0e",  # oranžová
    "practical-applications":   "#d62728",  # červená
    "CAPSTONE":                 "#FFFFFF",
}

# Alfa (průhlednost) pro poloprůhledné sektory
SECTOR_ALPHA = 0.18  # 0.15–0.25 vypadá nejlépe

# Výchozí offset pro štítek kategorie po směru větve (mapové jednotky)
LABEL_OFFSET_DEFAULT = 1.10

# ======================================================================================
# ROZLOŽENÍ – KONCENTRICKÉ KRUŽNICE + PARAMETRY GEOMETRIE
# ======================================================================================

CENTER_X, CENTER_Y = 0.0, 0.0

CAP_RING_R     = 0.72
CAP_RING_WIDTH = 12
CAP_ICON_SIZE  = 0.92

RING_START = 5.8            # první kružnice pro vnější uzly
RING_STEP  = 3.4            # krok mezi kružnicemi
LAST_RING_R = 6.8           # vynucené finální r pro okraj

# „Rozfoukávání“ větví a uzlů ortogonálně ke směru křivky (jemné oddělení)
ORTHO_FAN_BRANCH = 3.2
ORTHO_FAN_NODE   = 0.50

# Rozsah t parametru, v němž u křivky hledáme body (chceme vynechat blízké okolí středu)
T0, T1           = 0.06, 0.98

# ======================================================================================
# DYNAMICKÉ POŘADÍ TRATÍ (TRACKS) – bere se z roadmap["tracks"], fallback pořadí:
# ======================================================================================

FALLBACK_TRACK_ORDER = [
    "math-fundamentals",
    "programming",
    "finance-theory",
    "practical-applications",
]

# ======================================================================================
# HELPERY – práce s roadmap/progress
# ======================================================================================

def _nodes(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vrátí list uzlů z roadmap dictu (bez dalších filtrů)."""
    return list(roadmap.get("nodes", []))

def _track_list(roadmap: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vrátí list track objektů (id, name, optional color) v pořadí, v jakém jsou v JSON."""
    tracks = list(roadmap.get("tracks", []) or [])
    if tracks:
        return tracks
    # fallback – když by náhodou v roadmap nebyly definovány tracks
    return [{"id": t, "name": t.title(), "color": FALLBACK_CATEGORY_COLORS.get(t, "#888")} for t in FALLBACK_TRACK_ORDER]

def _track_order_ids(roadmap: Dict[str, Any]) -> List[str]:
    """Pořadí tracků podle roadmap["tracks"]; fallback na FALLBACK_TRACK_ORDER."""
    tr = _track_list(roadmap)
    if tr:
        return [t.get("id") for t in tr if t.get("id")]
    return list(FALLBACK_TRACK_ORDER)

def _track_id_to_name(roadmap: Dict[str, Any]) -> Dict[str, str]:
    """Mapování track_id → zobrazované jméno (name)."""
    out={}
    for t in _track_list(roadmap):
        tid = str(t.get("id", "")).strip()
        if tid:
            out[tid] = str(t.get("name", tid)).strip() or tid
    # fallbacky (kdyby něco chybělo)
    for k in FALLBACK_TRACK_ORDER:
        out.setdefault(k, k.title())
    out.setdefault("CAPSTONE", "Capstone")
    return out

def _track_id_to_color(roadmap: Dict[str, Any]) -> Dict[str, str]:
    """Mapování track_id → barva (hex); pokud není v JSON, vezme se z fallbacku."""
    out={}
    for t in _track_list(roadmap):
        tid = str(t.get("id", "")).strip()
        if not tid:
            continue
        col = t.get("color")
        if isinstance(col, str) and col.strip():
            out[tid] = col.strip()
    for k, v in FALLBACK_CATEGORY_COLORS.items():
        out.setdefault(k, v)
    return out

def _done_ids(progress: Dict[str, Any]) -> Set[str]:
    """Zkonzumuje progress a vrátí množinu dokončených ID."""
    p = progress or {}
    done=set()
    for nid, st in (p.get("tasks", {}) or {}).items():
        if st.get("test_passed"):
            done.add(str(nid))
    for nid in (p.get("completed", []) or []):
        done.add(str(nid))
    return done

def _node_status(node: Dict[str, Any], done: Set[str]) -> str:
    """Vrátí stav uzlu: done / available / locked."""
    nid=str(node.get("id"))
    if nid in done: return "done"
    prereqs=[str(p) for p in (node.get("prereqs", []) or [])]
    return "available" if all(p in done for p in prereqs) else "locked"

def _current_id(nodes: List[Dict[str, Any]], done: Set[str]) -> Optional[str]:
    """Najde první dostupný nedokončený uzel (kromě Capstone)."""
    for nd in nodes:
        nid=str(nd.get("id"))
        if nid == "capstone":
            continue
        if _node_status(nd, done)=="available" and nid not in done:
            return nid
    return None

# ======================================================================================
# IKONY
# ======================================================================================

def _icon_name(node: Dict[str, Any]) -> str:
    """Heuristika pro výběr ikon podle id/label/track."""
    nid = (node.get("id","") or "").lower()
    lbl = (node.get("label","") or "").lower()
    trk = (node.get("track","") or "").lower()
    direct = {"python_basics":"python","python":"python","numpy":"numpy","pandas":"pandas","plotly":"plotly"}
    if nid in direct: return direct[nid]
    combo = f"{nid} {lbl} {trk}"
    if any(k in combo for k in ["calc","linear","prob","stat","math","stoch","measure"]): return "math"
    if any(k in combo for k in ["ml","ai","model","learn","dl","gbm","xgb","lgbm"]):      return "ml"
    if any(k in combo for k in ["finance","market","alpha","factor","portfolio","risk","capm","var","es"]): return "finance"
    if any(k in combo for k in ["data","sql","parquet","arrow","etl","spark","stream","cloud"]): return "data"
    if "capstone" in combo: return "star"
    return "book"

def _image_layer(x: float, y: float, filename: str, sx: float, sy: float) -> Dict[str, Any]:
    """Vytvoří položku pro fig.update_layout(images=[...])."""
    return dict(
        source=f"{ICON_PATH}/{filename}{ICON_EXT}",
        xref="x", yref="y", x=x, y=y,
        sizex=sx, sizey=sy, xanchor="center", yanchor="middle",
        sizing="contain", layer="above", opacity=1.0,
    )

# ======================================================================================
# PROGRESS / PRSTENCE KOLEM UZLŮ
# ======================================================================================

def _node_progress_ratio(progress: Dict[str, Any], nid: str) -> float:
    """0..1 (zobrazení zeleného prstence progresu) – 1.0 pokud test_passed."""
    st=(progress or {}).get("tasks", {}).get(str(nid), {})
    all_t=st.get("tasks_all", []) or []
    done_t=st.get("tasks_done", []) or []
    base=0.7*(len(done_t)/max(1, len(all_t)))
    if st.get("test_passed"): base=1.0
    return float(max(0.0, min(1.0, base)))

def _ring_arc(cx: float, cy: float, r: float, frac: float, steps: int=140):
    """Vygeneruje oblouk prstence pro progress (část kružnice)."""
    if frac <= 0: return [], []
    theta0 = -math.pi/2
    thetas=[theta0 + 2*math.pi*frac*(k/steps) for k in range(steps+1)]
    xs=[cx + r*math.cos(t) for t in thetas]
    ys=[cy + r*math.sin(t) for t in thetas]
    return xs, ys

def _ring_full(cx: float, cy: float, r: float, steps: int=180):
    """Celý prstenec (bílý základ)."""
    return _ring_arc(cx, cy, r, 1.0, steps)

# ======================================================================================
# KATEGORIZACE – jen 4 kategorie, pořadí podle roadmap["tracks"]
# ======================================================================================

def _normalize_track_id(track_id: Optional[str]) -> str:
    """Vrátí čistý track_id (fallback na 'programming', pokud nic)."""
    if track_id and isinstance(track_id, str):
        return " ".join(track_id.split()).lower()
    return "programming"

def _group_tracks(roadmap: Dict[str,Any]) -> Dict[str, List[Dict[str,Any]]]:
    """
    Rozdělí uzly podle track_id (jen 4 kategorie).
    Pořadí klíčů odpovídá pořadí v roadmap["tracks"]; fallback na FALLBACK_TRACK_ORDER.
    """
    tracks: Dict[str,List[Dict[str,Any]]] = {}
    for n in _nodes(roadmap):
        tr = _normalize_track_id(n.get("track"))
        if tr == "capstone": 
            # capstone budeme přidávat až nakonec jako samostatný prvek
            continue
        m = dict(n); m["track"]=tr
        tracks.setdefault(tr, []).append(m)

    ordered: Dict[str,List[Dict[str,Any]]] = {}
    for key in _track_order_ids(roadmap):
        if key in tracks: ordered[key]=tracks.pop(key)
    # zbytek (neměl by být, ale pro jistotu):
    for key in sorted(tracks.keys()):
        ordered[key]=tracks[key]

    return ordered

# ======================================================================================
# GEOMETRIE VĚTVÍ – kubická Bézierova křivka přes 4 body
# ======================================================================================

def _bezier(p0, p1, p2, p3, t: float) -> Tuple[float,float]:
    u = 1.0 - t
    return (
        u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
        u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1],
    )

def _controls_for_angle(ang: float, far_r: float, branch_index: int):
    """
    Definuje řídící body pro větev v úhlu `ang` s maximálním dosahem `far_r`.
    Odděluje sousední větve pomocí ORTHO_FAN_BRANCH ortogonálně ke směru.
    """
    cx, cy = CENTER_X, CENTER_Y
    c, s = math.cos(ang), math.sin(ang)
    p3 = (cx + far_r*c, cy + far_r*s)
    s0 = CAP_RING_R + 1.0
    x0, y0 = cx + s0*c, cy + s0*s
    p0 = (x0, y0)
    ox, oy = -s, c
    side = 1 if (branch_index % 2 == 0) else -1
    p1 = (x0 + 0.28*far_r*c + ORTHO_FAN_BRANCH*ox*side,
          y0 + 0.28*far_r*s + ORTHO_FAN_BRANCH*oy*side)
    p2 = (cx + 0.66*far_r*c - ORTHO_FAN_BRANCH*1.05*ox*side,
          cy + 0.66*far_r*s - ORTHO_FAN_BRANCH*1.05*oy*side)
    return p0, p1, p2, p3

def _t_for_radius(p0, p1, p2, p3, r: float) -> float:
    """Najde t na křivce tak, aby vzdálenost od středu ≈ r (binární hledání)."""
    lo, hi = T0, T1
    cx, cy = CENTER_X, CENTER_Y
    for _ in range(42):
        mid = 0.5*(lo+hi)
        x, y = _bezier(p0,p1,p2,p3, mid)
        d = math.hypot(x - cx, y - cy)
        if d < r: lo = mid
        else:     hi = mid
    return 0.5*(lo+hi)

def _branch_points_on_rings(ang: float, n_nodes: int, branch_index: int):
    """
    Vrátí seznam bodů (x,y) na jednotlivých koncentrických kružnicích pro větev.
    Body leží na křivce definované řídícími body vypočtenými z ang a far_r.
    """
    if n_nodes <= 0:
        return []
    far_r = RING_START + (n_nodes - 1) * RING_STEP
    p0, p1, p2, p3 = _controls_for_angle(ang, far_r, branch_index)
    radii = [RING_START + k*RING_STEP for k in range(n_nodes)]
    radii.reverse()
    radii[-1] = LAST_RING_R
    pts=[]
    c, s = math.cos(ang), math.sin(ang)
    ox, oy = -s, c
    side   = 1 if (branch_index % 2 == 0) else -1
    for j, rj in enumerate(radii):
        t  = _t_for_radius(p0, p1, p2, p3, rj)
        spread_idx = (n_nodes - 1) - j
        p2k = (p2[0] + ORTHO_FAN_NODE*ox*side*spread_idx,
               p2[1] + ORTHO_FAN_NODE*oy*side*spread_idx)
        x, y = _bezier(p0, p1, p2k, p3, t)
        pts.append((x, y))
    return pts

def _layout_outer_ring(roadmap: Dict[str, Any]) -> List[Dict[str,Any]]:
    """
    Rozpočítá pozice všech uzlů na větvích:
    - větve v úhlech rovnoměrně dle pořadí tracků,
    - uzly na koncentrických kružnicích (vněji = pozdější),
    - do každého uzlu doplní __cat__ (track id), __branch_index__, __branch_angle__.
    Přidá capstone do středu.
    """
    trks = _group_tracks(roadmap)
    names = list(trks.keys())   # track_id v pořadí
    m = max(1, len(names))
    angles = [i*(2*math.pi)/m for i in range(m)]
    out=[]
    for i, track_id in enumerate(names):
        ang = angles[i]
        nodes = trks[track_id]
        pts  = _branch_points_on_rings(ang, len(nodes), i)
        for j, base in enumerate(nodes):
            n = dict(base)
            n["x"], n["y"] = pts[j]
            n["__cat__"]   = track_id
            n["__order__"] = j
            n["__branch_index__"] = i
            n["__branch_angle__"] = ang
            out.append(n)
    out.append({"id":"capstone","label":"Capstone","x":CENTER_X,"y":CENTER_Y,
                "__cat__":"CAPSTONE","__order__":999})
    return out

def _axis_ranges(nodes: List[Dict[str, Any]], pad: float=4.4):
    """Rozsahy os s paddingem pro pěkné orámování grafu."""
    xs=[float(n["x"]) for n in nodes] or [0.0]
    ys=[float(n["y"]) for n in nodes] or [0.0]
    return ((min(xs)-pad, max(xs)+pad), (min(ys)-pad, max(ys)+pad))

# ======================================================================================
# POMOCNÉ – VEKTORY, ŠTÍTKY, SEKTORY
# ======================================================================================

def _unit(vx: float, vy: float) -> Tuple[float, float]:
    """Jednotkový vektor."""
    L = math.hypot(vx, vy)
    return (vx / L, vy / L) if L else (0.0, 0.0)

def _label_pos_for_branch(points: List[Tuple[float, float]],
                          offset: float = LABEL_OFFSET_DEFAULT,
                          at_end: bool = True) -> Tuple[float, float]:
    """
    Vrátí pozici štítku kategorie posunutou ve směru posledního (nebo prvního) segmentu.
    """
    if len(points) < 2:
        return points[-1] if points else (CENTER_X, CENTER_Y)
    p2 = points[-1] if at_end else points[0]
    p1 = points[-2] if at_end else points[1]
    ux, uy = _unit(p2[0] - p1[0], p2[1] - p1[1])
    return p2[0] + ux * offset, p2[1] + uy * offset

def _sector_path(cx: float, cy: float,
                 r_inner: float, r_outer: float,
                 ang_start: float, ang_end: float) -> str:
    """
    SVG path pro prstencovou výseč (r_inner..r_outer, ang_start..ang_end), úhly v radiánech.
    Využíváme dvě obloukové části (outer + inner) a spoj (L).
    """
    while ang_end <= ang_start:
        ang_end += 2 * math.pi

    x1o, y1o = cx + r_outer * math.cos(ang_start), cy + r_outer * math.sin(ang_start)
    x2o, y2o = cx + r_outer * math.cos(ang_end),   cy + r_outer * math.sin(ang_end)
    x1i, y1i = cx + r_inner * math.cos(ang_end),   cy + r_inner * math.sin(ang_end)
    x2i, y2i = cx + r_inner * math.cos(ang_start), cy + r_inner * math.sin(ang_start)

    large_arc = 1 if (ang_end - ang_start) > math.pi else 0

    return (
        f"M {x1o},{y1o} "
        f"A {r_outer},{r_outer} 0 {large_arc},1 {x2o},{y2o} "
        f"L {x1i},{y1i} "
        f"A {r_inner},{r_inner} 0 {large_arc},0 {x2i},{y2i} Z"
    )

def _to_rgba(hex_color: str, alpha: float) -> str:
    """HEX → rgba(r,g,b,a) string (bez validace formátu)."""
    h = hex_color.strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) == 3:  # #abc
        h = "".join([c*2 for c in h])
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    a = max(0.0, min(1.0, float(alpha)))
    return f"rgba({r},{g},{b},{a})"

# ======================================================================================
# FIGURE – HLAVNÍ FUNKCE
# ======================================================================================

def make_figure(roadmap: Dict[str, Any],
                progress: Optional[Dict[str, Any]] = None,
                center_nid: Optional[str] = None,
                center_zoom: float = 4.6,
                celebrate_nid: Optional[str] = None,
                show_category_sectors: bool = True,
                category_label_at_end: bool = True,
                label_offset: float = LABEL_OFFSET_DEFAULT) -> go.Figure:
    """
    Vytvoří kompletní interaktivní graf roadmapy.
    - show_category_sectors: True = poloprůhledné sektory pod větvemi; False = textové štítky.
    - category_label_at_end: True = štítek na konci větve (směr ven); False = u středu (začátek).
    - label_offset: vzdálenost štítku od nejbližšího uzlu po tečně větve.
    """

    # Barvy a jména kategorií z roadmap
    track_colors = _track_id_to_color(roadmap)  # id → hex barva
    track_names  = _track_id_to_name(roadmap)   # id → zobrazované jméno

    # Rozmístění uzlů po větvích (koncentrické kružnice)
    nodes = _layout_outer_ring(roadmap)
    done = _done_ids(progress or {})
    current = _current_id(nodes, done)

    # Seskupení bodů větví + metadata pro kategorie
    branches: Dict[int,List[Tuple[float,float]]] = {}
    branch_cat: Dict[int, str] = {}
    branch_ang: Dict[int, float] = {}
    for nd in nodes:
        bi = nd.get("__branch_index__")
        if bi is None:
            continue
        branches.setdefault(bi, [])
        branches[bi].append((nd["x"], nd["y"]))
        branch_cat[bi] = str(nd.get("__cat__", ""))
        # přímý úhel větve od středu (podle posledního bodu)
        px, py = (nd["x"], nd["y"])
        branch_ang[bi] = math.atan2(py - CENTER_Y, px - CENTER_X)

    # Volitelná vrstva podkladových sektorů (poloprůhledné výseče)
    sector_shapes: List[Dict[str, Any]] = []
    if show_category_sectors and len(branches) >= 1:
        # Seřadit větve podle úhlu – sektor pro každou větev (kategorii) mezi polovinami sousedních úhlů
        ordered = sorted(branch_ang.items(), key=lambda kv: kv[1])
        order_keys = [k for k, _ in ordered]
        for i, bi in enumerate(order_keys):
            ang_c   = branch_ang[bi]
            ang_prev = branch_ang[order_keys[i - 1]]
            ang_next = branch_ang[order_keys[(i + 1) % len(order_keys)]]
            # Mezní úhly: střed mezi sousedy
            start = (ang_prev + ang_c) / 2.0
            end   = (ang_c + ang_next) / 2.0

            # Radiální rozsah: nechť nezačíná úplně u capstone a končí lehce za poslední uzly
            r_in  = CAP_RING_R + 0.85
            r_out = LAST_RING_R + 1.4

            cat_id = branch_cat.get(bi, "")
            hex_col = track_colors.get(cat_id, FALLBACK_CATEGORY_COLORS.get(cat_id, "#999999"))
            rgba    = _to_rgba(hex_col, SECTOR_ALPHA)

            sector_shapes.append(dict(
                type="path",
                path=_sector_path(CENTER_X, CENTER_Y, r_in, r_out, start, end),
                fillcolor=rgba,
                line=dict(width=0),
                layer="below",
            ))

    # ===== Traces (větve, stín větví, prstence, uzly) =====
    traces: List[go.Scatter] = []

    # větve (stín + barva větve)
    for bi, pts in branches.items():
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        color = BRANCH_COLORS[bi % len(BRANCH_COLORS)]
        # stín
        traces.append(go.Scatter(
            x=xs, y=[y-0.14 for y in ys], mode="lines",
            line=dict(color="rgba(15,22,40,0.75)", width=BRANCH_WIDTH+10),
            hoverinfo="skip", showlegend=False
        ))
        # hlavní linka větve
        traces.append(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=color, width=BRANCH_WIDTH, shape="spline"),
            hoverinfo="skip", showlegend=False
        ))

    # jen skutečné (ne-capstone) uzly
    core_nodes=[nd for nd in nodes if nd["id"]!="capstone"]

    # prstence – bílý základ
    base_rx, base_ry=[], []
    for nd in core_nodes:
        xs, ys = _ring_full(nd["x"], nd["y"], r=RING_RADIUS, steps=160)
        base_rx += xs + [None]; base_ry += ys + [None]
    traces.append(go.Scatter(x=base_rx, y=base_ry, mode="lines",
                             line=dict(color=RING_BASE_COLOR, width=RING_BASE_WIDTH, shape="spline"),
                             hoverinfo="skip", showlegend=False))

    # prstence – zelený progress
    prog_rx, prog_ry=[], []
    for nd in core_nodes:
        frac=_node_progress_ratio(progress or {}, str(nd.get("id")))
        if frac <= 0: continue
        xs, ys = _ring_arc(nd["x"], nd["y"], r=RING_RADIUS, frac=frac, steps=160)
        prog_rx += xs + [None]; prog_ry += ys + [None]
    traces.append(go.Scatter(x=prog_rx, y=prog_ry, mode="lines",
                             line=dict(color=RING_PROGRESS_COLOR, width=RING_PROGRESS_WIDTH, shape="spline"),
                             hoverinfo="skip", showlegend=False))

    # Barva výplně uzlu podle stavu
    def _fill(nd: Dict[str, Any]) -> str:
        st=_node_status(nd, done)
        if st=="done": return NODE_DONE
        if str(nd.get("id"))==current: return NODE_CURRENT
        if st=="available": return NODE_AVAILABLE
        return NODE_LOCKED

    # uzly
    traces.append(go.Scatter(
        x=[nd["x"] for nd in core_nodes],
        y=[nd["y"] for nd in core_nodes],
        mode="markers",
        marker=dict(size=[BASE_NODE_SIZE]*len(core_nodes),
                    color=[_fill(nd) for nd in core_nodes],
                    line=dict(width=0)),
        hovertemplate="<b>%{customdata[1]}</b><br><span style='color:#9fb4ff'>%{customdata[2]}</span><extra></extra>",
        customdata=[[str(nd.get("id")), str(nd.get("label", nd.get("id"))), str(track_names.get(nd.get('__cat__'), nd.get('__cat__')))] for nd in core_nodes],
        showlegend=False
    ))

    # capstone – prstenec uprostřed
    cx, cy = CENTER_X, CENTER_Y
    cap_x, cap_y = _ring_full(cx, cy, r=CAP_RING_R, steps=200)
    traces.append(go.Scatter(
        x=cap_x, y=cap_y, mode="lines",
        line=dict(color="#FFFFFF", width=CAP_RING_WIDTH, shape="spline"),
        hoverinfo="skip", showlegend=False
    ))

    # ikony (capstone + per-node)
    images=[_image_layer(cx, cy, "star", CAP_ICON_SIZE, CAP_ICON_SIZE)]
    for nd in core_nodes:
        images.append(_image_layer(nd["x"], nd["y"], _icon_name(nd), ICON_SIZE_X, ICON_SIZE_Y))
        if _node_status(nd, done)=="locked":
            images.append(_image_layer(nd["x"], nd["y"], "lock", ICON_SIZE_X, ICON_SIZE_Y))

    # rozsahy os
    (xr0,xr1),(yr0,yr1)=_axis_ranges(nodes, pad=4.6)
    if center_nid:
        try:
            c = next(nd for nd in nodes if str(nd.get("id"))==str(center_nid))
            xr0,xr1 = c["x"]-center_zoom, c["x"]+center_zoom
            yr0,yr1 = c["y"]-center_zoom, c["y"]+center_zoom
        except StopIteration:
            pass

    # Figure
    fig = go.Figure(data=traces)

    # shapes – bezpečné přidání (list vs tuple)
    if sector_shapes:
        existing_shapes = list(fig.layout.shapes or [])
        fig.update_layout(shapes=existing_shapes + sector_shapes)

    # Štítky kategorií – jen pokud NEzobrazujeme sektory
    annots = []
    if not show_category_sectors:
        for bi, pts in branches.items():
            cat = branch_cat.get(bi, "")
            if not cat:
                continue
            lx, ly = _label_pos_for_branch(pts,
                                           offset=label_offset,
                                           at_end=category_label_at_end)
            bg_hex = track_colors.get(cat, FALLBACK_CATEGORY_COLORS.get(cat, "#888888"))
            # pro text dáme sytý podklad, text bílý
            annots.append(dict(
                x=lx, y=ly,
                text=str(track_names.get(cat, cat)),
                showarrow=False,
                font=dict(color="#ffffff", size=13),
                bgcolor=bg_hex,
                bordercolor="rgba(0,0,0,0.25)",
                borderwidth=1,
                borderpad=4,
                opacity=0.98
            ))

    # fixní legenda nahoře – „chips“ zařídíme v CSS, zde jen legend entries:
    legend_items: List[go.Scatter] = []
    for track_id in _track_order_ids(roadmap):
        if track_id == "CAPSTONE": 
            continue
        name = track_names.get(track_id, track_id.title())
        col  = track_colors.get(track_id, FALLBACK_CATEGORY_COLORS.get(track_id, "#bbb"))
        legend_items.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=14, color=col, line=dict(width=1, color="rgba(0,0,0,0.25)")),
            name=name,
            hoverinfo="skip",
            showlegend=True
        ))
    # přidat legendu do figure (musí být součástí data)
    for tr in legend_items:
        fig.add_trace(tr)

    # annotations – bezpečné přidání
    existing_ann = list(fig.layout.annotations or [])
    fig.update_layout(
        template="none",
        paper_bgcolor=BG_COLOR, plot_bgcolor=PLOT_BG,
        margin=dict(l=16,r=16,t=24,b=16),
        xaxis=dict(range=[xr0,xr1], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[yr0,yr1], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1.0),
        hovermode="closest",
        showlegend=True,
        images=images,
        uirevision="quant-tree-rings-v4",   # stabilita zoomu/panu mezi callbacky
        dragmode="pan",
        transition=dict(duration=0),
        annotations=existing_ann + annots,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.04,
            xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=12),
            itemclick=False, itemdoubleclick=False
        ),
    )
    return fig

# ======================================================================================
# STRÁNKA + ROUTER (Dash layout)
# ======================================================================================

def build_layout(fig: go.Figure) -> html.Div:
    """
    Router:
    - "/"        → roadmap (graf)
    - "/lesson"  → viewer Markdownu
    Pozor: UI třídy (className) očekávají existující CSS (neposíláme zde CSS).
    """
    # ----- Home (graf) -----
    home_page = html.Div(
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
                    style={"height": "82vh"},
                ),
                className="graph-col",
            ),

            # Toast (tooltip) pro zamčené uzly
            html.Div(
                [
                    html.Span(id="lock-toast-text"),
                    html.Button("×", id="lock-toast-close", n_clicks=0, className="toast-close"),
                ],
                id="lock-toast",
                className="toast",
                style={"display": "none"},
            ),

            # === MODAL ===
            html.Div(
                [
                    html.Div(
                        [
                            # Head: titulek + progress donut
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="modal-title", className="modal-title"),
                                            html.Div(id="modal-estimate", className="modal-estimate"),
                                        ],
                                        className="modal-head-left",
                                    ),
                                    html.Div(
                                        dcc.Graph(
                                            id="modal-progress",
                                            figure=go.Figure(),
                                            config={"displayModeBar": False},
                                            style={"height": "96px", "width": "96px"}
                                        ),
                                        className="modal-head-right",
                                    ),
                                ],
                                className="modal-head"
                            ),

                            # Popis + odkazy
                            html.Div(id="modal-desc", className="modal-desc"),
                            html.Div(id="modal-links", className="modal-links"),

                            html.Hr(),

                            # Témata (místo checklistu)
                            html.Div("Témata", className="side-subtitle"),
                            html.Ul(id="topics-list", className="topics-list"),

                            # Stav testu (jen info)
                            html.Div(id="test-status", className="test-status"),

                            html.Div(
                                [
                                    html.A("✖ Zavřít", href="/", className="btn"),
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
        id="home-page",
        className="page-wrap",
    )

    # ----- Lesson viewer -----
    lesson_page = html.Div(
        [
            html.Div(
                [
                    html.A("← Zpět na roadmapu", href="/", className="btn"),
                    html.Button("✔ Označit lekci jako hotovou", id="btn-complete-lesson", className="btn success"),
                ],
                className="panel sticky",
            ),
            html.Div(
                [
                    html.Div(id="lesson-title", className="lesson-title"),
                    html.Div(id="lesson-meta", className="lesson-meta"),
                    html.Hr(),
                    dcc.Markdown(id="lesson-md", className="lesson-md"),
                    html.Hr(),
                    html.Div(
                        [
                            html.A("◀ Předchozí téma", id="lesson-prev", href="#", className="btn"),
                            html.A("Další téma ▶", id="lesson-next", href="#", className="btn"),
                        ],
                        className="lesson-nav"
                    )
                ],
                className="lesson-card"
            ),
        ],
        id="lesson-page",
        className="page-wrap",
        style={"display": "none"},
    )

    # Router
    return html.Div(
        [
            dcc.Location(id="url"),
            home_page,
            lesson_page
        ]
    )

# ======================================================================================
# KONEC SOUBORU
# ======================================================================================
