# core/progress.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta, date

# timezone
try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Prague")
except Exception:
    _TZ = None

PROGRESS_PATH = Path("core/data/progress.json")


# ------------------ time helpers ------------------
def _today_date() -> date:
    return datetime.now(_TZ).date() if _TZ else date.today()

def _today_str() -> str:
    return _today_date().isoformat()

def _yesterday_str() -> str:
    d = _today_date() - timedelta(days=1)
    return d.isoformat()


# ------------------ defaults / io ------------------
def _default_progress() -> Dict:
    return {
        "xp": 0,
        "level": 1,
        "completed_nodes": [],      # list[str]
        "streak_days": 0,
        "last_day": None,           # YYYY-MM-DD
        "badges": [],               # list[str]
        # per-task stav
        "tasks": {},                # { "<node_id>": {"tasks_done":[int,...]} }
        # DENNÍ CÍL (XP) + log
        "daily_goal_xp": 30,
        "daily_log": {}             # { "YYYY-MM-DD": { "xp": int, "completed_nodes":[str,...] } }
    }

def load_progress() -> Dict:
    if PROGRESS_PATH.exists():
        try:
            with PROGRESS_PATH.open(encoding="utf-8") as f:
                p = json.load(f)
            p.setdefault("completed_nodes", [])
            p.setdefault("xp", 0)
            p.setdefault("level", 1)
            p.setdefault("streak_days", 0)
            p.setdefault("last_day", None)
            p.setdefault("badges", [])
            p.setdefault("tasks", {})
            p.setdefault("daily_goal_xp", 30)
            p.setdefault("daily_log", {})
            return p
        except Exception:
            pass
    return _default_progress()

def save_progress(p: Dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)


# ------------------ daily goal helpers ------------------
def get_daily_goal() -> int:
    return int(load_progress().get("daily_goal_xp", 30))

def set_daily_goal(xp_target: int) -> Dict:
    p = load_progress()
    p["daily_goal_xp"] = max(0, int(xp_target))
    save_progress(p)
    return p

def _ensure_today_log(p: Dict) -> Dict:
    t = _today_str()
    log = p.setdefault("daily_log", {})
    day = log.setdefault(t, {"xp": 0, "completed_nodes": []})
    day.setdefault("xp", 0)
    day.setdefault("completed_nodes", [])
    return day

def today_xp() -> int:
    p = load_progress()
    day = p.get("daily_log", {}).get(_today_str(), {"xp": 0})
    return int(day.get("xp", 0))

def is_goal_met_today() -> bool:
    return today_xp() >= get_daily_goal()

def _bump_streak(p: Dict) -> Dict:
    today = _today_str()
    last = p.get("last_day")
    if last == today:
        return p
    if last is None:
        p["streak_days"] = 1
    else:
        p["streak_days"] = int(p.get("streak_days", 0)) + 1 if last == _yesterday_str() else 1
    p["last_day"] = today
    return p


# ------------------ XP ------------------
def _add_xp_internal(p: Dict, amount: int) -> Tuple[Dict, bool]:
    """
    Přičte XP do profilu i do dnešního logu.
    Vrací (progress, goal_just_achieved).
    """
    amount = int(amount)
    before_goal_met = today_xp() >= p.get("daily_goal_xp", 30)

    # global xp
    p["xp"] = int(p.get("xp", 0)) + amount
    p["level"] = p["xp"] // 100 + 1

    # daily xp
    day = _ensure_today_log(p)
    day["xp"] = int(day.get("xp", 0)) + amount

    after_goal_met = (day["xp"] >= p.get("daily_goal_xp", 30))
    goal_just_achieved = (not before_goal_met) and after_goal_met

    save_progress(p)
    return p, goal_just_achieved

def add_xp(amount: int) -> Dict:
    p = load_progress()
    p, _ = _add_xp_internal(p, amount)
    return p


# ------------------ node completion ------------------
def completed_set() -> Set[str]:
    return set(map(str, load_progress().get("completed_nodes", [])))

def is_completed(node_id: str) -> bool:
    return str(node_id) in completed_set()

def mark_completed(node_id: str, xp_award: int = 10) -> Tuple[Dict, bool]:
    """
    Označí uzel jako hotový (pokud ještě není), připíše XP,
    aktualizuje streak a denní log.
    Vrací (progress, goal_just_achieved_today).
    """
    node_id = str(node_id)
    p = load_progress()
    comp: List[str] = list({str(x) for x in p.get("completed_nodes", [])})

    if node_id not in comp:
        comp.append(node_id)
        p["completed_nodes"] = comp
        # přidat i do denního logu seznam completed node ids
        day = _ensure_today_log(p)
        if node_id not in day["completed_nodes"]:
            day["completed_nodes"].append(node_id)

        # XP + daily goal
        p, goal_hit = _add_xp_internal(p, xp_award)
    else:
        goal_hit = False

    p = _bump_streak(p)
    save_progress(p)
    return p, goal_hit


# ------------------ per-task progress ------------------
def _ensure_task_bucket(p: Dict, node_id: str) -> Dict:
    tasks = p.setdefault("tasks", {})
    b = tasks.setdefault(str(node_id), {})
    b.setdefault("tasks_done", [])
    return b

def get_tasks_done(node_id: str) -> Set[int]:
    b = load_progress().get("tasks", {}).get(str(node_id), {})
    return set(b.get("tasks_done", []))

def set_task_done(node_id: str, task_index: int, done: bool) -> Dict:
    p = load_progress()
    b = _ensure_task_bucket(p, str(node_id))
    done_list: List[int] = list({int(i) for i in b.get("tasks_done", [])})
    if done and task_index not in done_list:
        done_list.append(int(task_index))
    if not done and task_index in done_list:
        done_list.remove(int(task_index))
    b["tasks_done"] = sorted(done_list)
    save_progress(p)
    return p

def node_progress_ratio(node: Dict) -> float:
    if is_completed(node["id"]):
        return 1.0
    all_tasks = node.get("tasks_all") or []
    if not all_tasks:
        return 0.0
    done_idx = get_tasks_done(node["id"])
    return max(0.0, min(1.0, len(done_idx) / len(all_tasks)))

def evaluate_node_completion(node: Dict, xp_award: int = 10) -> Tuple[bool, Dict, bool]:
    """
    Pokud jsou VŠECHNY úkoly uzlu hotové, označí uzel completed (+XP).
    Vrací (just_completed, progress, goal_just_achieved_today)
    """
    if is_completed(node["id"]):
        return False, load_progress(), False
    all_tasks = node.get("tasks_all") or []
    if not all_tasks:
        return False, load_progress(), False
    done_idx = get_tasks_done(node["id"])
    if len(done_idx) >= len(all_tasks):
        p, goal_hit = mark_completed(node["id"], xp_award=xp_award)
        return True, p, goal_hit
    return False, load_progress(), False


# ------------------ availability / category progress ------------------
def first_available_index(nodes: List[Dict]) -> int:
    comp = completed_set()
    for i, n in enumerate(nodes):
        nid = str(n["id"])
        if nid in comp:
            continue
        prereqs = [str(x) for x in (n.get("prereqs") or [])]
        if all(pr in comp for pr in prereqs):
            return i
    return 0

def category_progress_from_nodes(nodes: List[Dict]) -> Dict[str, int]:
    total = len(nodes)
    if total <= 0:
        return {"total": 0, "done": 0, "pct": 0}
    comp = completed_set()
    done = sum(1 for n in nodes if str(n["id"]) in comp)
    pct = int(round(100 * done / total))
    return {"total": total, "done": done, "pct": pct}


# ------------------ badges ------------------
XP_BADGES = [100, 500, 1000]
STREAK_BADGES = [3, 7, 14, 30]

def _badge_id_xp(th: int) -> str: return f"xp_{th}"
def _badge_id_streak(th: int) -> str: return f"streak_{th}"
def _badge_id_cat(track_id: str) -> str: return f"cat_{track_id}_done"

def _compute_category_done_ids(roadmap: Dict) -> List[str]:
    comp = completed_set()
    done_tracks: List[str] = []
    for t in roadmap.get("tracks", []):
        tid = t["id"]
        tnodes = [n for n in roadmap.get("nodes", []) if n.get("track") == tid]
        if tnodes and all(str(n["id"]) in comp for n in tnodes):
            done_tracks.append(tid)
    return done_tracks

def recompute_badges(roadmap: Dict) -> Tuple[Dict, List[str]]:
    p = load_progress()
    owned: Set[str] = set(p.get("badges", []))
    new_set: Set[str] = set(owned)

    xp = int(p.get("xp", 0))
    for th in XP_BADGES:
        if xp >= th:
            new_set.add(_badge_id_xp(th))

    streak = int(p.get("streak_days", 0))
    for th in STREAK_BADGES:
        if streak >= th:
            new_set.add(_badge_id_streak(th))

    for tid in _compute_category_done_ids(roadmap):
        new_set.add(_badge_id_cat(tid))

    newly_awarded = sorted(list(new_set - owned))
    if newly_awarded:
        p["badges"] = sorted(list(new_set))
        save_progress(p)
    return p, newly_awarded
