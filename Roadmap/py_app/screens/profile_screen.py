from __future__ import annotations
import flet as ft
from typing import List, Dict, Tuple

from py_app.core.models import Roadmap
from py_app.core.progress import load_progress, category_progress_from_nodes
from py_app.ui.appbar import build_appbar

COLORS = getattr(ft, "colors", getattr(ft, "Colors", None))  # kompat vrstva

# Přátelštější názvy & emoji pro odznaky
BADGE_META: Dict[str, Tuple[str, str]] = {
    # XP
    "xp_100":  ("🟡", "100 XP"),
    "xp_500":  ("🟠", "500 XP"),
    "xp_1000": ("🟣", "1000 XP"),
    # Streak
    "streak_3":  ("🔥", "3 dny v řadě"),
    "streak_7":  ("🔥🔥", "7 dní v řadě"),
    "streak_14": ("🔥🔥🔥", "14 dní v řadě"),
    "streak_30": ("🔥 x30", "30 dní v řadě"),
}

def _pretty_track_label(bid: str, roadmap: Roadmap) -> Tuple[str, str] | None:
    # očekává formát "track_<id>_complete"
    if not bid.startswith("track_") or not bid.endswith("_complete"):
        return None
    tid = bid[len("track_"):-len("_complete")]
    for t in roadmap.tracks:
        if t.id == tid:
            return ("🏁", f"Dokončeno: {t.name}")
    # fallback – kdyby track chyběl
    return ("🏁", f"Dokončeno: {tid}")

def _progress_bar(pct: int, width: int = 260, height: int = 10, color=None) -> ft.Stack:
    color = color or getattr(COLORS, "GREEN_ACCENT_700", COLORS.GREEN)
    pct = max(0, min(100, pct))
    bg = ft.Container(width=width, height=height,
                      bgcolor=COLORS.with_opacity(0.12, COLORS.GREY_600),
                      border_radius=999)
    fg = ft.Container(width=int(width * pct / 100), height=height,
                      bgcolor=color, border_radius=999)
    return ft.Stack([bg, fg])

def _badge_card(emoji: str, label: str) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(12, 10),
        border_radius=12,
        bgcolor=COLORS.with_opacity(0.06, COLORS.ON_SURFACE),
        content=ft.Row(
            [
                ft.Container(
                    width=32, height=32, border_radius=999,
                    bgcolor=COLORS.with_opacity(0.10, COLORS.PRIMARY),
                    alignment=ft.alignment.center,
                    content=ft.Text(emoji, size=18),
                ),
                ft.Text(label, weight=ft.FontWeight.W_600),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

def _badges_grid(roadmap: Roadmap) -> ft.Control:
    p = load_progress()
    ids: List[str] = list(p.get("badges", []))
    if not ids:
        return ft.Text("Zatím žádné odznaky — plň lekce a vracej se denně! 😊")

    # převeď ID → (emoji, label)
    items: List[ft.Control] = []
    for bid in sorted(ids):
        meta = BADGE_META.get(bid)
        if meta is None:
            meta = _pretty_track_label(bid, roadmap)
        if meta is None:
            # fallback – neupravené ID
            items.append(_badge_card("🏅", bid))
        else:
            items.append(_badge_card(meta[0], meta[1]))

    return ft.ResponsiveRow(
        [ft.Container(ctrl, col={"xs": 12, "sm": 6, "md": 4, "lg": 3}) for ctrl in items],
        columns=12, spacing=10, run_spacing=10
    )

def create_profile_view(page: ft.Page, roadmap: Roadmap) -> ft.View:
    p = load_progress()

    # Hlava (Avatar + text)
    avatar = ft.Container(
        width=64, height=64, border_radius=999,
        bgcolor=COLORS.with_opacity(0.10, COLORS.PRIMARY),
        alignment=ft.alignment.center,
        content=ft.Text("Q", size=28, weight=ft.FontWeight.W_800),
    )
    head = ft.Row(
        [
            avatar,
            ft.Column(
                [
                    ft.Text("Quant Learner", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Sbírej XP a drž si streak 🔥", color=COLORS.GREY_500)
                ],
                spacing=2
            )
        ],
        spacing=16
    )

    # Hlavní statistiky
    stats = ft.Row(
        [
            ft.Column([ft.Text("Úroveň"), ft.Text(str(p.get("level", 1)), size=22, weight=ft.FontWeight.W_700)],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.VerticalDivider(opacity=0.08),
            ft.Column([ft.Text("XP"), ft.Text(str(p.get("xp", 0)), size=22, weight=ft.FontWeight.W_700)],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.VerticalDivider(opacity=0.08),
            ft.Column([ft.Text("Streak"), ft.Text(f"{p.get('streak_days', 0)} 🔥", size=22, weight=ft.FontWeight.W_700)],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
    )

    # Per-kategorie progress
    per_category_rows: List[ft.Control] = []
    for tr in roadmap.tracks:
        nodes = [n for n in roadmap.nodes if n.track == tr.id]
        prog = category_progress_from_nodes([n.model_dump() for n in nodes])  # pydantic -> dict
        row = ft.Row(
            [
                ft.Text(tr.name, width=220),
                _progress_bar(prog["pct"]),
                ft.Text(f"{prog['done']}/{prog['total']}  ({prog['pct']}%)",
                        width=140, text_align=ft.TextAlign.RIGHT),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        per_category_rows.append(row)

    content = ft.Column(
        [
            head,
            ft.Divider(opacity=0.1),
            stats,
            ft.Divider(opacity=0.1),
            ft.Text("Odznaky", size=16, weight=ft.FontWeight.BOLD),
            _badges_grid(roadmap),
            ft.Divider(opacity=0.1),
            ft.Text("Postup podle kategorií", size=16, weight=ft.FontWeight.BOLD),
            ft.Column(per_category_rows, spacing=8),
        ],
        spacing=16
    )

    # >>> náš kompatibilní “appbar”
    appbar = build_appbar(title=ft.Text("Profil", size=18, weight=ft.FontWeight.W_700))

    return ft.View(
        route="/profile",
        controls=[appbar, ft.Container(content=content, padding=16)],
    )
