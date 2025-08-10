import flet as ft
import math
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set

from py_app.ui.appbar import build_appbar
from py_app.core.progress import (
    load_progress, mark_completed, first_available_index, category_progress_from_nodes,
    set_task_done, get_tasks_done, node_progress_ratio, evaluate_node_completion,
    recompute_badges, get_daily_goal, today_xp
)

DATA_PATH = Path("py_app/core/data/roadmap.json")
AUDIO_PATH = "sounds/fanfare.mp3"

COLORS = ft.Colors

# ---------- micro-anim helpers ----------
def _animate_bg_on_hover(ctrl: ft.Container, base, hover):
    def _h(e: ft.HoverEvent):
        ctrl.bgcolor = hover if e.data == "true" else base
        ctrl.animate = ft.animation.Animation(140, "easeOut")
        ctrl.update()
    return _h

def _press_scale_handlers(ctrl: ft.Control, pressed_scale: float = 0.98):
    def down(_):
        if hasattr(ctrl, "scale"):
            ctrl.animate_scale = ft.animation.Animation(80, "easeOut")
            ctrl.scale = pressed_scale
            ctrl.update()
    def up(_):
        if hasattr(ctrl, "scale"):
            ctrl.animate_scale = ft.animation.Animation(80, "easeOut")
            ctrl.scale = 1.0
            ctrl.update()
    return down, up

def _ripple_in(stack: ft.Stack, x: float, y: float, color, max_radius: int = 240, dur_ms: int = 330):
    dot = ft.Container(
        left=x, top=y, width=12, height=12,
        bgcolor=color, border_radius=999, opacity=0.18,
        animate=ft.animation.Animation(dur_ms, "easeOut"),
        animate_opacity=ft.animation.Animation(dur_ms, "easeOut"),
    )
    stack.controls.insert(0, dot)
    stack.update()
    dot.left = x - max_radius
    dot.top = y - max_radius
    dot.width = max_radius * 2
    dot.height = max_radius * 2
    dot.opacity = 0.0
    stack.update()

    def _cleanup(_=None):
        try:
            stack.controls.remove(dot)
            stack.update()
        except Exception:
            pass
    stack.page.run_task_later(dur_ms / 1000.0, _cleanup, None)

# =========================
#  GEOMETRIE (S-křivka)
# =========================
def _s_curve_points(n: int, width: int = 860, height: int = 560, amp: float = 160.0, margin: int = 90) -> List[Tuple[float, float]]:
    if n <= 1:
        return [(width/2, height/2)]
    pts: List[Tuple[float, float]] = []
    step = (width - 2 * margin) / (n - 1)
    for i in range(n):
        x = margin + i * step
        t = i / (n - 1)
        y = height/2 + amp * math.sin(t * math.pi * (1.6 if n <= 5 else 2.0))
        pts.append((x, y))
    return pts

def _track_color(track_id: str, data: Dict) -> str:
    for t in data.get("tracks", []):
        if t["id"] == track_id:
            return t.get("color") or "#888888"
    return "#888888"

# =========================
#  CATEGORY SCREEN
# =========================
class CategoryScreen(ft.View):
    def __init__(self, page: ft.Page, category_id: str, category_name: str, on_back):
        super().__init__(route=f"/category/{category_id}")
        self.page = page
        self.category_id = category_id
        self.category_name = category_name
        self.on_back = on_back

        self.data = self._load_data()
        self._id2label = {str(n["id"]): n.get("label", str(n["id"])) for n in self.data.get("nodes", [])}
        self.nodes: List[Dict] = [n for n in self.data["nodes"] if n["track"] == self.category_id]
        self.points: List[Tuple[float, float]] = _s_curve_points(len(self.nodes))
        self.focus_idx: Optional[int] = None

        # refs
        self._bubble_refs: List[ft.Container] = []
        self._aura_refs: List[ft.Container] = []
        self._bubble_stacks: List[ft.Stack] = []  # pro ripple
        self._pulse_running = False
        self._confetti_layer: Optional[ft.Stack] = None

        # vlnění spojů
        self._wave_dots: List[Tuple[ft.Control, float, float, float, float, float]] = []
        self._wave_running = False
        self._wave_amp = 8.0

        # audio
        self._audio: Optional[ft.Audio] = None

        self._recompute_statuses()
        self._build_view()

    # ---------- data ----------
    def _load_data(self) -> Dict:
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Soubor {DATA_PATH} neexistuje.")
        with DATA_PATH.open(encoding="utf-8") as f:
            return json.load(f)

    def _recompute_statuses(self):
        p = load_progress()
        completed = set(map(str, p.get("completed_nodes", [])))
        for n in self.nodes:
            nid = str(n["id"])
            if nid in completed:
                n["__status__"] = "completed"
            else:
                prereqs = [str(x) for x in (n.get("prereqs") or [])]
                n["__status__"] = "available" if all(pr in completed for pr in prereqs) else "locked"
            n["__ratio__"] = node_progress_ratio(n)

    def _missing_prereqs(self, node: Dict) -> List[str]:
        p = load_progress()
        done: Set[str] = set(map(str, p.get("completed_nodes", [])))
        req = [str(x) for x in (node.get("prereqs") or [])]
        missing_ids = [r for r in req if r not in done]
        return [self._id2label.get(r, r) for r in missing_ids]

    # =========================
    #  CONFETTI + AUDIO
    # =========================
    def _spawn_confetti(self, duration: float = 1.2, count: int = 40):
        if not self._confetti_layer:
            self._confetti_layer = ft.Stack([], expand=True)
            self.page.overlay.append(self._confetti_layer)
            self.page.update()

        w, h = 860, 560
        colors = [
            COLORS.AMBER, COLORS.LIGHT_BLUE, COLORS.LIGHT_GREEN,
            COLORS.PINK, COLORS.CYAN, COLORS.DEEP_ORANGE, COLORS.LIME
        ]
        bits: List[ft.Container] = []
        for _ in range(count):
            x = random.randint(20, w - 20)
            size = random.randint(6, 12)
            color = random.choice(colors)
            bit = ft.Container(
                width=size, height=size,
                bgcolor=color, border_radius=random.choice([2, 4, 999]),
                left=x, top=-20,
                animate_position=ft.animation.Animation(int(duration*1000), "easeOut"),
                animate_opacity=ft.animation.Animation(int(duration*1000), "easeOut"),
                opacity=1.0,
            )
            bits.append(bit)
            self._confetti_layer.controls.append(bit)

        self._confetti_layer.update()

        for bit in bits:
            target_y = random.randint(int(h*0.35), int(h*0.9))
            bit.top = target_y
            bit.left = bit.left + random.randint(-40, 40)
            self._confetti_layer.update()

        def _fade_out(_):
            for bit in bits:
                bit.opacity = 0.0
            self._confetti_layer.update()

            def _cleanup(__):
                for bit in bits:
                    try:
                        self._confetti_layer.controls.remove(bit)
                    except Exception:
                        pass
                self._confetti_layer.update()
            self.page.run_task_later(0.5, _cleanup, None)

        self.page.run_task_later(duration * 0.9, _fade_out, None)

    def _ensure_audio(self):
        if self._audio is not None:
            return
        self._audio = ft.Audio(src=AUDIO_PATH, volume=0.9, autoplay=False)
        self.page.overlay.append(self._audio)
        self.page.update()

    def _play_fanfare(self):
        try:
            self._ensure_audio()
            self._audio.play()
        except Exception:
            pass

    # =========================
    #  UI
    # =========================
    def _build_view(self):
        # mini „Dnes“ (XP) → extra_left do AppBaru
        goal = get_daily_goal()
        txp = today_xp()
        pct = (txp / goal) if goal > 0 else 1.0
        bar_bg = ft.Container(width=160, height=8, bgcolor=COLORS.with_opacity(0.12, COLORS.PRIMARY), border_radius=999)
        bar_fg = ft.Container(width=int(160 * pct), height=8, bgcolor=COLORS.GREEN_ACCENT_700, border_radius=999)
        extra_left = ft.Row(
            [ft.Text("Dnes:"), ft.Stack([bar_bg, bar_fg]), ft.Text(f"{txp}/{goal} XP", size=12, color=COLORS.GREY_600)],
            spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        self.continue_btn = ft.ElevatedButton(
            "▶ Pokračovat", icon=ft.Icons.PLAY_ARROW, on_click=self._on_continue,
            bgcolor=COLORS.GREEN_ACCENT_700, color=COLORS.BLACK,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        self.badges_btn = ft.OutlinedButton("🏅 Odznaky", on_click=self._open_badges)

        appbar = build_appbar(
            title=ft.Text(self.category_name, size=18, weight=ft.FontWeight.W_700),
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
            extra_left=extra_left,
            extra_actions=[self.continue_btn, self.badges_btn],
        )

        self.canvas = self._build_canvas()
        self.tasks_panel = self._build_tasks_panel()

        # Panel s hover zvýrazněním
        panel = ft.Container(
            content=ft.ResponsiveRow(
                [
                    ft.Container(self.canvas, col={"xs": 12, "md": 8}),
                    ft.Container(self.tasks_panel, col={"xs": 12, "md": 4}),
                ],
                columns=12, spacing=10, run_spacing=10
            ),
            padding=12, expand=True,
            bgcolor=COLORS.with_opacity(0.02, COLORS.ON_SURFACE),
            border_radius=14,
        )
        panel.on_hover = _animate_bg_on_hover(panel,
                                              COLORS.with_opacity(0.02, COLORS.ON_SURFACE),
                                              COLORS.with_opacity(0.04, COLORS.ON_SURFACE))

        self.controls = [appbar, panel]
        self._start_pulse()
        self._start_wave_animation()

    def _build_canvas(self) -> ft.Stack:
        w, h = 860, 560
        base = [ft.Container(width=w, height=h, bgcolor=COLORS.with_opacity(0.04, COLORS.PRIMARY), border_radius=14)]

        # SPOJE tenká linka
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]; x2, y2 = self.points[i + 1]
            base.append(
                ft.Container(
                    left=min(x1, x2), top=min(y1, y2),
                    content=ft.Container(
                        width=abs(x2 - x1) or 2, height=abs(y2 - y1) or 2,
                        bgcolor=COLORS.with_opacity(0.25, COLORS.GREY_500),
                        border_radius=8,
                    )
                )
            )

        # bubliny + aury s tactile efekty
        self._bubble_refs = []
        self._bubble_stacks = []
        self._aura_refs = []

        for i, (node, (x, y)) in enumerate(zip(self.nodes, self.points)):
            status = node["__status__"]
            ratio = node["__ratio__"]
            col = _track_color(node["track"], self.data)

            fill = (COLORS.with_opacity(0.25, COLORS.GREY_700) if status == "locked"
                    else COLORS.GREEN_400 if status == "available"
                    else COLORS.GREEN_ACCENT_700)
            ring = COLORS.GREY_800 if status == "locked" else col
            pct_txt = "100%" if status == "completed" else f"{int(round(ratio*100))}%"
            focused = (i == self.focus_idx)
            scale = 1.15 if focused else 1.0

            aura = ft.Container(
                width=120, height=56,
                border_radius=999,
                bgcolor=COLORS.with_opacity(0.06, col) if focused else COLORS.TRANSPARENT,
            )
            self._aura_refs.append(aura)

            inner = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(node["label"], size=12, weight=ft.FontWeight.BOLD, color=COLORS.WHITE),
                        ft.Text(pct_txt, size=10, color=COLORS.GREY_300),
                    ],
                    spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10, border_radius=999, bgcolor=fill,
                border=ft.border.all(3, ring),
            )
            # ripple stack
            st = ft.Stack([inner], width=120, height=56)
            bubble = ft.Container(content=st, animate_scale=ft.animation.Animation(120, "easeOut"), scale=scale)

            # hover → jemné zvýraznění a zvětšení
            def _hover_b(e: ft.HoverEvent, idx=i):
                if idx == self.focus_idx:
                    return
                bubble.scale = 1.06 if e.data == "true" else 1.0
                bubble.update()

            bubble.on_hover = _hover_b
            self._bubble_refs.append(bubble)
            self._bubble_stacks.append(st)

            # gesture – press, ripple, click
            d, u = _press_scale_handlers(bubble, 0.97)

            def _down(e: ft.TapEvent, idx=i):
                d(e)
                _ripple_in(self._bubble_stacks[idx], e.local_x, e.local_y, COLORS.PRIMARY, 120, 260)

            def _up(e):
                u(e)

            def _tap(e, idx=i):
                self._on_bubble_click(idx)

            gest = ft.GestureDetector(content=bubble, on_tap=_tap, on_tap_down=_down, on_tap_up=_up)

            base.append(ft.Container(left=x - 60, top=y - 28, content=aura))
            base.append(ft.Container(left=x - 60, top=y - 26, content=gest))

        # vlnící tečky (pod bublinami)
        dots = self._make_wave_dots()
        base = [base[0]] + dots + base[1:]

        return ft.Stack(base, width=w, height=h)

    def _make_wave_dots(self) -> List[ft.Control]:
        pos_controls: List[ft.Control] = []
        n_dots_per_segment = 14
        dot_size = 6
        dot_color = COLORS.with_opacity(0.55, COLORS.BLUE_GREY_300)

        for i in range(len(self.points) - 1):
            (x1, y1), (x2, y2) = self.points[i], self.points[i + 1]
            dx, dy = (x2 - x1), (y2 - y1)
            L = math.hypot(dx, dy) or 1.0
            nx, ny = (-dy / L, dx / L)

            for k in range(n_dots_per_segment):
                s = (k + 1) / (n_dots_per_segment + 1)
                bx = x1 + s * dx
                by = y1 + s * dy
                phase = random.random() * 2 * math.pi

                dot = ft.Container(width=dot_size, height=dot_size, bgcolor=dot_color, border_radius=999)
                pos = ft.Container(left=bx - dot_size/2, top=by - dot_size/2, content=dot)

                self._wave_dots.append((pos, bx, by, nx, ny, phase))
                pos_controls.append(pos)

        return pos_controls

    def _build_tasks_panel(self) -> ft.Column:
        self.tasks_title = ft.Text("Vyber uzel z mapy", size=16, weight=ft.FontWeight.W_700)
        self.tasks_info = ft.Text("", size=12, color=COLORS.GREY_600)
        self.tasks_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        self.complete_btn = ft.FilledButton(
            "✔ Označit jako hotové", icon=ft.Icons.CHECK_CIRCLE,
            on_click=self._on_complete_clicked, disabled=True
        )
        # hover/press highlight celého panelu úkolů
        panel = ft.Column(
            [self.tasks_title, self.tasks_info, ft.Divider(opacity=0.1), self.tasks_list, ft.Divider(opacity=0.1), self.complete_btn],
            spacing=12
        )
        wrapper = ft.Container(content=panel, padding=10, border_radius=12,
                               bgcolor=COLORS.with_opacity(0.02, COLORS.ON_SURFACE))
        wrapper.on_hover = _animate_bg_on_hover(wrapper,
                                                COLORS.with_opacity(0.02, COLORS.ON_SURFACE),
                                                COLORS.with_opacity(0.04, COLORS.ON_SURFACE))
        return wrapper

    # =========================
    #  INTERAKCE
    # =========================
    def _on_bubble_click(self, idx: int):
        node = self.nodes[idx]
        if node["__status__"] == "locked":
            b = self._bubble_refs[idx]
            b.animate_offset = ft.animation.Animation(100, "easeInOut")
            b.offset = ft.Offset(-0.02, 0); b.update()
            def _back(_):
                b.offset = ft.Offset(0.02, 0); b.update()
                def _center(__):
                    b.offset = ft.Offset(0, 0); b.update()
                self.page.run_task_later(0.1, _center, None)
            self.page.run_task_later(0.08, _back, None)

            missing = self._missing_prereqs(node)
            if missing:
                self._xp_toast(text="🔒 Uzamčeno", sub="Nejdřív splň: " + " • ".join(missing))
            self._load_tasks_locked(node, missing)
            return

        self._focus_node(idx)

    def _focus_node(self, idx: int):
        self.focus_idx = idx
        self._refresh_canvas()
        self._load_tasks_for(idx)

    def _refresh_canvas(self):
        self._recompute_statuses()
        self.points = _s_curve_points(len(self.nodes))

        new_stack = self._build_canvas()
        self.canvas.controls = new_stack.controls
        self.canvas.update()

        self._start_pulse()
        self._start_wave_animation()

    def _load_tasks_locked(self, node: Dict, missing_labels: List[str]):
        self.tasks_title.value = f"🔒 {node['label']}"
        self.tasks_info.value = "Uzamčeno. Chybí: " + ", ".join(missing_labels) if missing_labels else "Uzamčeno."
        self.tasks_list.controls = []
        self.complete_btn.disabled = True
        self.update()

    def _task_checkbox(self, node_id: str, i: int, label: str, checked: bool) -> ft.Control:
        cb = ft.Checkbox(label=label, value=checked)
        # ripple při kliknutí do řádku
        row = ft.Row([cb], alignment=ft.MainAxisAlignment.START)
        stack = ft.Stack([ft.Container(content=row, padding=8)], expand=True)
        wrapper = ft.Container(content=stack, border_radius=8,
                               bgcolor=COLORS.with_opacity(0.02, COLORS.ON_SURFACE))
        wrapper.on_hover = _animate_bg_on_hover(wrapper,
                                                COLORS.with_opacity(0.02, COLORS.ON_SURFACE),
                                                COLORS.with_opacity(0.05, COLORS.ON_SURFACE))

        def _on_change(e):
            set_task_done(node_id, i, cb.value)
            just_completed, _, goal_hit = evaluate_node_completion(
                next(n for n in self.nodes if str(n["id"]) == str(node_id)), xp_award=10
            )
            self._refresh_canvas()
            if just_completed:
                with DATA_PATH.open(encoding="utf-8") as f:
                    roadmap = json.load(f)
                _, newly = recompute_badges(roadmap)
                msg_parts = ["✨ Uzel dokončen!", "🪙 +10 XP"]
                if goal_hit:
                    msg_parts.append("🎯 Denní cíl splněn!")
                if newly:
                    msg_parts.append("🏅 " + " • ".join(newly))
                self._xp_toast(" | ".join(msg_parts))
                self._spawn_confetti()
                self._play_fanfare()

        cb.on_change = _on_change

        def _down(e: ft.TapEvent):
            _ripple_in(stack, e.local_x, e.local_y, COLORS.PRIMARY, 180, 300)

        return ft.GestureDetector(content=wrapper, on_tap_down=_down)

    def _load_tasks_for(self, idx: int):
        node = self.nodes[idx]
        self.tasks_title.value = f"📚 {node['label']}"
        self.tasks_info.value = ""
        tasks = node.get("tasks_all") or []
        done_set = get_tasks_done(node["id"])

        self.tasks_list.controls = [
            self._task_checkbox(node["id"], i, t, i in done_set)
            for i, t in enumerate(tasks)
        ]
        self.complete_btn.disabled = not (node["__status__"] != "locked" and node["__ratio__"] < 1.0)
        self.update()

    def _on_continue(self, e):
        idx = first_available_index(self.nodes)
        self._focus_node(idx)
        self._xp_toast("➡️ Pokračuj tady")

    def _on_complete_clicked(self, e):
        if self.focus_idx is None:
            return
        node = self.nodes[self.focus_idx]
        if node["__status__"] == "locked":
            self._xp_toast("🔒 Nejdřív odemkni předchozí uzly")
            return

        _, goal_hit = mark_completed(str(node["id"]), xp_award=10)
        with DATA_PATH.open(encoding="utf-8") as f:
            roadmap = json.load(f)
        _, newly = recompute_badges(roadmap)

        self._recompute_statuses()
        self._load_tasks_for(self.focus_idx)
        self._refresh_canvas()

        msg_parts = ["✨ Hotovo!", "🪙 +10 XP"]
        if goal_hit:
            msg_parts.append("🎯 Denní cíl splněn!")
        if newly:
            msg_parts.append("🏅 " + " • ".join(newly))
        self._xp_toast(" | ".join(msg_parts))
        self._spawn_confetti()
        self._play_fanfare()

    # =========================
    #  MINI UX HELPERS
    # =========================
    def _xp_toast(self, text: str, sub: Optional[str] = None):
        row = ft.Row([ft.Text(text)], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        content = ft.Column([ft.Text(text), ft.Text(sub, size=12, color=COLORS.GREY_400)], spacing=2) if sub else row
        self.page.snack_bar = ft.SnackBar(content, open=True)
        self.page.update()

    def _start_pulse(self):
        if self._pulse_running:
            return
        self._pulse_running = True

        def step(scale_up: bool = True):
            if not self._bubble_refs:
                self._pulse_running = False
                return
            try:
                for i, node in enumerate(self.nodes):
                    if node["__status__"] == "available" and i != self.focus_idx:
                        b = self._bubble_refs[i]
                        target = 1.06 if scale_up else 1.0
                        b.animate_scale = ft.animation.Animation(280, "easeOut")
                        b.scale = target
                if self._bubble_refs:
                    self.canvas.update()
            except Exception:
                self._pulse_running = False
                return

            self.page.run_task_later(0.55, lambda _: step(not scale_up), None)

        self.page.run_task_later(0.2, lambda _: step(True), None)

    def _start_wave_animation(self):
        if self._wave_running:
            return
        self._wave_running = True

        def tick(_=None, t: float = 0.0):
            if not self._wave_dots:
                self._wave_running = False
                return
            try:
                t += 0.22
                A = self._wave_amp
                for (pos, bx, by, nx, ny, phase) in self._wave_dots:
                    off = A * math.sin(t + phase)
                    pos.left = bx - 3 + nx * off
                    pos.top = by - 3 + ny * off
                self.canvas.update()
            except Exception:
                self._wave_running = False
                return

            self.page.run_task_later(0.06, lambda __: tick(_, t), None)

        self.page.run_task_later(0.06, tick, None)

    # =========================
    #  BADGE CENTER
    # =========================
    def _open_badges(self, e):
        p = load_progress()
        owned = set(p.get("badges", []))
        xp = int(p.get("xp", 0))
        streak = int(p.get("streak_days", 0))

        xp_thresholds = [100, 500, 1000]
        streak_thresholds = [3, 7, 14, 30]

        tracks = self.data.get("tracks", [])
        comp = set(map(str, p.get("completed_nodes", [])))

        def track_done(tid: str) -> bool:
            tnodes = [n for n in self.data.get("nodes", []) if n.get("track") == tid]
            return bool(tnodes) and all(str(n["id"]) in comp for n in tnodes)

        def chip(text: str, ok: bool):
            return ft.Container(
                padding=ft.padding.symmetric(10, 8),
                border_radius=999,
                bgcolor=COLORS.AMBER if ok else COLORS.with_opacity(0.08, COLORS.GREY),
                content=ft.Text(text, weight=ft.FontWeight.W_600, color=COLORS.BLACK if ok else COLORS.GREY_600)
            )

        xp_row = ft.Row([chip(f"XP {th}", xp >= th) for th in xp_thresholds], spacing=8, wrap=True)
        streak_row = ft.Row([chip(f"🔥 {th}", streak >= th) for th in streak_thresholds], spacing=8, wrap=True)
        cat_row = ft.Row([chip(f"{t['name']}", track_done(t["id"])) for t in tracks], spacing=8, wrap=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🏅 Odznaky", weight=ft.FontWeight.W_700),
            content=ft.Column(
                [
                    ft.Text("Získané / dostupné milníky", color=COLORS.GREY_600),
                    ft.Text("XP", weight=ft.FontWeight.W_700),
                    xp_row,
                    ft.Text("Streak", weight=ft.FontWeight.W_700),
                    streak_row,
                    ft.Text("Kategorie", weight=ft.FontWeight.W_700),
                    cat_row,
                ],
                tight=True, spacing=8, scroll=ft.ScrollMode.AUTO, height=360, width=520
            ),
            actions=[ft.TextButton("Zavřít", on_click=lambda e: self._close_dialog())],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

def create_category_screen(page, category_id, category_name, on_back):
    return CategoryScreen(page, category_id, category_name, on_back)
