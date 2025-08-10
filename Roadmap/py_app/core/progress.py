# py_app/core/progress.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Iterable
import json
import datetime as dt

# ====== Cesty ======
_PROGRESS_PATH = Path("py_app/core/data/progress.json")
_BACKUP_DIR = _PROGRESS_PATH.parent / "progress_backups"

# ====== Interní helpery ======
def _today_str() -> str:
    return dt.date.today().isoformat()

def _yesterday_str() -> str:
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()

def _default_progress() -> Dict[str, Any]:
    now = dt.datetime.utcnow().isoformat()
    return {
        "xp": 0,
        "level": 1,
        "streak_days": 0,
        "last_day": None,            # "YYYY-MM-DD" kdy byl poslední zisk XP/aktivita
        "daily_goal": 50,
        "completed_nodes": [],       # list[str]
        "tasks": {},                 # { node_id: { "tasks_done":[int,...], "completed": bool } }
        "badges": [],                # list[str]
        "recent": [],                # list[ { "date": "YYYY-MM-DD", "type":"xp|node", "amount":int, "id": str } ]
        "meta": {"created": now, "last_updated": now, "version": 1}
    }

def _read_progress_file() -> Dict[str, Any]:
    try:
        if _PROGRESS_PATH.exists():
            data = json.loads(_PROGRESS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # doplníme chybějící klíče (migrace)
                base = _default_progress()
                for k, v in base.items():
                    if k not in data:
                        data[k] = v
                if "meta" not in data:
                    data["meta"] = {"created": dt.datetime.utcnow().isoformat(),
                                    "last_updated": dt.datetime.utcnow().isoformat(),
                                    "version": 1}
                return data
    except Exception as e:
        print(f"[PROGRESS] Chyba čtení: {e}")
    return _default_progress()

def _write_progress_file(data: Dict[str, Any], backup: bool = True) -> None:
    try:
        _PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data.setdefault("meta", {})
        data["meta"]["last_updated"] = dt.datetime.utcnow().isoformat()

        if backup and _PROGRESS_PATH.exists():
            _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            ts = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            (_BACKUP_DIR / f"progress_{ts}.json").write_text(
                json.dumps(_read_progress_file(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        _PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[PROGRESS] Chyba zápisu: {e}")

# ====== Veřejné utility (export/import/reset) ======
def export_progress() -> Dict[str, Any]:
    return _read_progress_file()

def import_progress(obj: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError("Importovaný objekt není dict.")
    if overwrite:
        _write_progress_file(obj)
        return obj

    cur = _read_progress_file()
    merged = dict(cur)

    merged["xp"] = max(int(cur.get("xp", 0)), int(obj.get("xp", 0)))
    merged["level"] = max(int(cur.get("level", 1)), int(obj.get("level", 1)))
    merged["streak_days"] = max(int(cur.get("streak_days", 0)), int(obj.get("streak_days", 0)))
    merged["last_day"] = obj.get("last_day", cur.get("last_day"))
    merged["daily_goal"] = int(obj.get("daily_goal", cur.get("daily_goal", 50)))

    a = set(map(str, cur.get("completed_nodes", [])))
    b = set(map(str, obj.get("completed_nodes", [])))
    merged["completed_nodes"] = sorted(a | b)

    mt = dict(cur.get("tasks", {}))
    for nid, bucket in (obj.get("tasks", {}) or {}).items():
        nid = str(nid)
        mb = mt.get(nid, {"tasks_done": [], "completed": False})
        done_set = set(mb.get("tasks_done", [])) | set(bucket.get("tasks_done", []))
        mb["tasks_done"] = sorted(map(int, done_set))
        mb["completed"] = bool(mb.get("completed")) or bool(bucket.get("completed"))
        mt[nid] = mb
    merged["tasks"] = mt

    ba = set(cur.get("badges", []))
    bb = set(obj.get("badges", []))
    merged["badges"] = sorted(ba | bb)

    ra = list(cur.get("recent", []))
    rb = list(obj.get("recent", []))
    merged["recent"] = (rb + ra)[-50:]

    _write_progress_file(merged)
    return merged

def reset_progress(full_reset: bool = True) -> None:
    if full_reset:
        _write_progress_file(_default_progress())
    else:
        cur = _read_progress_file()
        cur.update({
            "xp": 0, "level": 1, "streak_days": 0, "last_day": None,
            "completed_nodes": [], "tasks": {}, "recent": []
        })
        _write_progress_file(cur)

# ====== ZPĚTNÁ KOMPATIBILITA + aplikační logika ======
# Tyto funkce volají tvoje obrazovky: home_screen.py, category_screen.py

def load_progress() -> Dict[str, Any]:
    """Zpětně kompatibilní – vrátí dict s průběhem."""
    return _read_progress_file()

def save_progress(data: Dict[str, Any]) -> None:
    _write_progress_file(data)

def get_daily_goal() -> int:
    return int(_read_progress_file().get("daily_goal", 50))

def set_daily_goal(v: int) -> None:
    p = _read_progress_file()
    p["daily_goal"] = int(max(0, v))
    _write_progress_file(p)

def _record_xp_event(amount: int, node_id: Optional[str] = None) -> None:
    """Zapíše XP událost do recent + udržuje streak."""
    if amount <= 0:
        return
    p = _read_progress_file()

    # streak update
    today = _today_str()
    last_day = p.get("last_day")
    if last_day is None or last_day != today:
        # nový den → pokud poslední den byl včera, inkrementuj streak, jinak reset na 1
        if last_day == _yesterday_str():
            p["streak_days"] = int(p.get("streak_days", 0)) + 1
        else:
            p["streak_days"] = 1
        p["last_day"] = today

    p["xp"] = int(p.get("xp", 0)) + int(amount)
    # jednoduchý level-up: každých 100 XP nová úroveň
    p["level"] = max(1, p["xp"] // 100 + 1)

    p.setdefault("recent", [])
    p["recent"].append({
        "date": today,
        "type": "xp",
        "amount": int(amount),
        "id": str(node_id) if node_id is not None else None
    })
    p["recent"] = p["recent"][-50:]

    _write_progress_file(p)

def today_xp() -> int:
    p = _read_progress_file()
    today = _today_str()
    total = 0
    for ev in p.get("recent", []):
        if ev.get("type") == "xp" and ev.get("date") == today:
            total += int(ev.get("amount", 0))
    return total

def get_tasks_done(node_id: str) -> List[int]:
    p = _read_progress_file()
    bucket = p.get("tasks", {}).get(str(node_id), {})
    return [int(i) for i in bucket.get("tasks_done", [])]

def set_task_done(node_id: str, index: int, done: bool) -> Dict[str, Any]:
    p = _read_progress_file()
    nid = str(node_id)
    p.setdefault("tasks", {})
    p["tasks"].setdefault(nid, {"tasks_done": [], "completed": False})
    s = set(map(int, p["tasks"][nid]["tasks_done"]))
    if done:
        s.add(int(index))
    else:
        s.discard(int(index))
    p["tasks"][nid]["tasks_done"] = sorted(s)
    _write_progress_file(p)
    return p["tasks"][nid]

def node_progress_ratio(node: Dict[str, Any]) -> float:
    tasks_all = node.get("tasks_all") or []
    if not tasks_all:
        # uzel bez úkolů – bereme hotové jen po označení completed
        p = _read_progress_file()
        return 1.0 if str(node.get("id")) in set(map(str, p.get("completed_nodes", []))) else 0.0
    done = set(get_tasks_done(node.get("id")))
    r = len(done) / max(1, len(tasks_all))
    return max(0.0, min(1.0, float(r)))

def evaluate_node_completion(node: Dict[str, Any], xp_award: int = 10) -> Tuple[bool, List[str], bool]:
    """
    Vrátí (just_completed, newly_unlocked_ids, goal_hit).
    newly_unlocked necháváme prázdné (logika odemykání je v UI), ale držíme signaturu.
    """
    p = _read_progress_file()
    nid = str(node.get("id"))
    tasks_all = node.get("tasks_all") or []
    done_set = set(get_tasks_done(nid))
    already_completed = nid in set(map(str, p.get("completed_nodes", [])))

    just_completed = (not already_completed) and (len(tasks_all) > 0) and (len(done_set) == len(tasks_all))
    goal_hit = False

    if just_completed:
        p["completed_nodes"] = sorted(set(map(str, p.get("completed_nodes", []))) | {nid})
        p.setdefault("tasks", {}).setdefault(nid, {"tasks_done": [], "completed": False})
        p["tasks"][nid]["completed"] = True
        _write_progress_file(p)
        # XP + denní cíl
        _record_xp_event(xp_award, node_id=nid)
        goal_hit = today_xp() >= get_daily_goal()

    return just_completed, [], goal_hit

def mark_completed(node_id: str, xp_award: int = 10) -> Tuple[bool, bool]:
    """
    Označí uzel jako hotový bez ohledu na tasks_all.
    Vrátí (was_completed_now, goal_hit).
    """
    p = _read_progress_file()
    nid = str(node_id)
    already = nid in set(map(str, p.get("completed_nodes", [])))
    goal_hit = False

    if not already:
        p["completed_nodes"] = sorted(set(map(str, p.get("completed_nodes", []))) | {nid})
        p.setdefault("tasks", {}).setdefault(nid, {"tasks_done": [], "completed": True})
        p["tasks"][nid]["completed"] = True
        _write_progress_file(p)
        _record_xp_event(xp_award, node_id=nid)
        goal_hit = today_xp() >= get_daily_goal()
        return True, goal_hit
    return False, today_xp() >= get_daily_goal()

def first_available_index(nodes: List[Dict[str, Any]]) -> int:
    """Najde první uzel se statusem 'available', jinak první ne-hotový, jinak 0."""
    p = _read_progress_file()
    completed = set(map(str, p.get("completed_nodes", [])))
    for i, n in enumerate(nodes):
        st = n.get("__status__")
        if st == "available":
            return i
    for i, n in enumerate(nodes):
        if str(n.get("id")) not in completed:
            return i
    return 0

def category_progress_from_nodes(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Vypočítá agregovaný postup pro kategorii:
      - total: počet všech tasků (sum přes nodes[].tasks_all)
      - done : počet splněných tasků
      - pct  : procenta (zaokrouhlená)
    Pokud node nemá tasks_all, počítáme jej jako 0/0; pokud je completed, přičteme 1/1.
    """
    p = _read_progress_file()
    completed = set(map(str, p.get("completed_nodes", [])))
    total = 0
    done = 0
    for n in nodes:
        nid = str(n.get("id"))
        tasks = n.get("tasks_all") or []
        if tasks:
            total += len(tasks)
            done += len(set(get_tasks_done(nid)))
        else:
            # bez úkolů – pokud completed, ber 1/1 jinak 0/1?
            # Abychom nedeformovali metriky, započítáme jen pokud chceme uzly bez úkolů vidět:
            total += 1
            done += 1 if nid in completed else 0
    pct = int(round((done / total) * 100)) if total > 0 else 0
    return {"total": total, "done": done, "pct": pct}

# ====== Odznaky ======
def _candidate_badges(roadmap: Optional[Any]) -> List[str]:
    """
    Vytvoří seznam možných odznaků (ID).
    - XP: 100, 500, 1000
    - Streak: 3, 7, 14, 30
    - Kategorie: 'track_<id>_complete'
    """
    out: List[str] = ["xp_100", "xp_500", "xp_1000", "streak_3", "streak_7", "streak_14", "streak_30"]
    if roadmap:
        for t in getattr(roadmap, "tracks", []):
            out.append(f"track_{t.id}_complete")
    return out

def recompute_badges(roadmap: Optional[Any] = None) -> Tuple[List[str], List[str]]:
    """
    Přepočítá odznaky dle aktuálního stavu.
    Vrací (všechny_možné, nově_udělené) — nové se rovnou uloží do progress.
    """
    p = _read_progress_file()
    owned = set(p.get("badges", []))
    possible = set(_candidate_badges(roadmap))

    newly: List[str] = []

    # XP thresholds
    xp = int(p.get("xp", 0))
    for th, bid in [(100, "xp_100"), (500, "xp_500"), (1000, "xp_1000")]:
        if xp >= th and bid not in owned:
            newly.append(bid)

    # Streak thresholds
    streak = int(p.get("streak_days", 0))
    for th, bid in [(3, "streak_3"), (7, "streak_7"), (14, "streak_14"), (30, "streak_30")]:
        if streak >= th and bid not in owned:
            newly.append(bid)

    # Kategorie kompletní
    if roadmap:
        completed = set(map(str, p.get("completed_nodes", [])))
        for t in roadmap.tracks:
            t_nodes = [n for n in roadmap.nodes if n.track == t.id]
            if t_nodes and all(str(n.id) in completed for n in t_nodes):
                bid = f"track_{t.id}_complete"
                if bid not in owned:
                    newly.append(bid)

    # Ulož
    if newly:
        p["badges"] = sorted(owned | set(newly))
        _write_progress_file(p)

    return sorted(possible), newly

# ====== Extra „rychlé“ akce ======
def add_xp(amount: int) -> None:
    _record_xp_event(int(amount))

def add_badge(badge_id: str) -> None:
    p = _read_progress_file()
    if badge_id not in p.get("badges", []):
        p.setdefault("badges", []).append(badge_id)
        _write_progress_file(p)

def mark_task_done(node_id: str, task_id: int) -> None:
    cur = set(get_tasks_done(node_id))
    cur.add(int(task_id))
    set_task_done(node_id, int(task_id), True)

from datetime import datetime

def get_today_progress() -> float:
    """
    Vrací dnešní progres jako číslo 0.0 – 1.0 podle počtu splněných úkolů.
    """
    data = _read_progress_file()
    tasks = data.get("tasks", {})
    completed = sum(len(v.get("tasks_done", [])) for v in tasks.values())
    # Předpokládejme max. 5 úkolů jako základní cíl
    return min(completed / 5, 1.0)


def get_current_streak() -> int:
    """
    Vrací počet dní v řadě, kdy byl splněn denní cíl.
    """
    data = _read_progress_file()
    return int(data.get("streak_days", 0))
