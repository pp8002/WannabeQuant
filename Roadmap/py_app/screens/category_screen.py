# screens/category_screen.py
import flet as ft
import math
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from core.progress import (
    load_progress, mark_completed, first_available_index, category_progress_from_nodes,
    set_task_done, get_tasks_done, node_progress_ratio, evaluate_node_completion, recompute_badges
)

DATA_PATH = Path("core/data/roadmap.json")


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


class CategoryScreen(ft.View):
    def __init__(self, page: ft.Page, category_id: str, category_name: str, on_back):
        super().__init__(route=f"/category/{category_id}")
        self.page = page
        self.category_id = category_id
        self.category_name = category_name
        self.on_back = on_back

        self.data = self._load_data()
        self.nodes: List[Dict] = [n for n in self.data["nodes"] if n["track"] == self.category_id]
        self.points: List[Tuple[float, float]] = _s_curve_points(len(self.nodes))
        self.focus_idx: Optional[int] = None
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

    # ---------- UI ----------
    def _build_view(self):
        # progress bar v hlavičce
        self.progress_label = ft.Text("", size=12, color=ft.colors.GREY_500)
        self.progress_fill = ft.Container(bgcolor=ft.colors.GREEN_ACCENT_700, height=10, width=0, border_radius=999)
        self.progress_bar = ft.Container(
            bgcolor=ft.colors.with_opacity(0.12, ft.colors.GREY_600),
            border_radius=999,
            padding=2,
            content=ft.Stack(controls=[self.progress_fill], height=10),
            width=200,
        )

        self.continue_btn = ft.ElevatedButton(
            "▶ Pokračovat",
            icon=ft.icons.PLAY_ARROW,
            on_click=self._on_continue,
            bgcolor=ft.colors.GREEN_ACCENT_700,
            color=ft.colors.BLACK,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        header = ft.AppBar(
            title=ft.Row(
                [ft.Text(self.category_name), ft.Container(width=12), self.progress_bar, ft.Container(width=8), self.progress_label],
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda e: self.on_back()),
            actions=[self.continue_btn],
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        self.canvas = self._build_canvas()
        self.tasks_panel = self._build_tasks_panel()

        self.controls = [
            header,
            ft.Container(
                content=ft.ResponsiveRow(
                    [
                        ft.Container(self.canvas, col={"xs": 12, "md": 8}),
                        ft.Container(self.tasks_panel, col={"xs": 12, "md": 4}),
                    ],
                    columns=12, spacing=10, run_spacing=10
                ),
                padding=12, expand=True
            )
        ]

        self._update_category_progress_ui(animated=False)

    def _build_canvas(self) -> ft.Stack:
        w, h = 860, 560
        base = [ft.Container(width=w, height=h, bgcolor=ft.colors.with_opacity(0.04, ft.colors.PRIMARY), border_radius=14)]

        # linky
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]; x2, y2 = self.points[i + 1]
            base.append(ft.Positioned(
                left=min(x1, x2), top=min(y1, y2),
                content=ft.Container(
                    width=abs(x2 - x1) or 2, height=abs(y2 - y1) or 2,
                    bgcolor=ft.colors.with_opacity(0.35, ft.colors.GREY_500),
                    border_radius=8,
                )
            ))

        # bubliny
        for i, (node, (x, y)) in enumerate(zip(self.nodes, self.points)):
            status = node["__status__"]
            ratio = node["__ratio__"]
            col = _track_color(node["track"], self.data)
            fill = (ft.colors.with_opacity(0.25, ft.colors.GREY_700) if status == "locked"
                    else ft.colors.GREEN_400 if status == "available"
                    else ft.colors.GREEN_ACCENT_700)
            ring = ft.colors.GREY_800 if status == "locked" else col
            pct_txt = "100%" if status == "completed" else f"{int(round(ratio*100))}%"
            focused = (i == self.focus_idx)
            scale = 1.15 if focused else 1.0

            bubble = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(node["label"], size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Text(pct_txt, size=10, color=ft.colors.GREY_300),
                    ],
                    spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10, border_radius=999, bgcolor=fill,
                border=ft.border.all(3, ring),
                animate_scale=ft.animation.Animation(200, "easeOut"),
                scale=scale,
                on_click=lambda e, idx=i: self._focus_node(idx)
            )
            base.append(ft.Positioned(left=x - 60, top=y - 26, content=bubble))

        return ft.Stack(base, width=w, height=h)

    def _build_tasks_panel(self) -> ft.Column:
        self.tasks_title = ft.Text("Vyber uzel z mapy", size=16, weight=ft.FontWeight.W_700)
        self.tasks_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        self.complete_btn = ft.FilledButton(
            "✔ Označit jako hotové", icon=ft.icons.CHECK_CIRCLE,
            on_click=self._on_complete_clicked, disabled=True
        )
        return ft.Column([self.tasks_title, ft.Divider(opacity=0.1), self.tasks_list, ft.Divider(opacity=0.1), self.complete_btn],
                         spacing=12)

    # ---------- interakce ----------
    def _focus_node(self, idx: int):
        self.focus_idx = idx
        self._refresh_canvas()
        self._load_tasks_for(idx)

    def _refresh_canvas(self):
        self._recompute_statuses()
        self.points = _s_curve_points(len(self.nodes))
        self.canvas.controls = self._build_canvas().controls
        self.canvas.update()
        self._update_category_progress_ui(animated=True)

    def _load_tasks_for(self, idx: int):
        node = self.nodes[idx]
        self.tasks_title.value = f"📚 {node['label']}"
        tasks = node.get("tasks_all") or []
        done_set = get_tasks_done(node["id"])

        def make_cb(i: int, label: str, checked: bool):
            def _on_change(e):
                set_task_done(node["id"], i, e.control.value)
                just_completed, _, goal_hit = evaluate_node_completion(node, xp_award=10)
                self._refresh_canvas()
                if just_completed:
                    with DATA_PATH.open(encoding="utf-8") as f:
                        roadmap = json.load(f)
                    _, newly = recompute_badges(roadmap)
                    msg = "Uzel dokončen! +10 XP 🎉"
                    if goal_hit:
                        msg += "  Denní cíl splněn ✅"
                    if newly:
                        msg += "  Nové odznaky: " + " • ".join(newly)
                    self.page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
                    self.page.update()
            return ft.Checkbox(label=label, value=checked, on_change=_on_change)

        self.tasks_list.controls = [make_cb(i, t, i in done_set) for i, t in enumerate(tasks)]
        self.complete_btn.disabled = not (node["__status__"] == "available" and node["__ratio__"] < 1.0)
        self.update()

    def _on_continue(self, e):
        idx = first_available_index(self.nodes)
        self._focus_node(idx)
        self.page.snack_bar = ft.SnackBar(ft.Text("Pokračuj tady ✨"), open=True)
        self.page.update()

    def _on_complete_clicked(self, e):
        if self.focus_idx is None:
            return
        node = self.nodes[self.focus_idx]
        _, goal_hit = mark_completed(str(node["id"]), xp_award=10)
        with DATA_PATH.open(encoding="utf-8") as f:
            roadmap = json.load(f)
        _, newly = recompute_badges(roadmap)
        self._recompute_statuses()
        self._load_tasks_for(self.focus_idx)
        self._refresh_canvas()
        msg = "Hotovo! +10 XP 🎉"
        if goal_hit:
            msg += "  Denní cíl splněn ✅"
        if newly:
            msg += "  Nové odznaky: " + " • ".join(newly)
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        self.page.update()


def create_category_screen(page, category_id, category_name, on_back):
    return CategoryScreen(page, category_id, category_name, on_back)
