# screens/profile_screen.py
import flet as ft
from typing import List, Dict
from core.models import Roadmap
from core.progress import load_progress, category_progress_from_nodes

# Mapování ID odznaků → (emoji, label)
BADGE_META: Dict[str, tuple[str, str]] = {
    # XP
    "xp_100": ("🔰", "100 XP"),
    "xp_500": ("💎", "500 XP"),
    "xp_1000": ("🏆", "1000 XP"),
    # Streak
    "streak_3": ("🔥", "3denní streak"),
    "streak_7": ("🔥🔥", "7denní streak"),
    "streak_14": ("🔥🔥🔥", "14denní streak"),
    "streak_30": ("🔥 x30", "30denní streak"),
    # Kategorie (generické – pokud přijde nepopsané ID, zobrazíme bez labelu)
}


def _progress_bar(pct: int, width: int = 220, height: int = 12, color=ft.colors.PRIMARY) -> ft.Container:
    fill_w = int(width * max(0, min(100, pct)) / 100)
    return ft.Container(
        width=width,
        height=height,
        bgcolor=ft.colors.with_opacity(0.12, ft.colors.GREY_600),
        border_radius=999,
        padding=2,
        content=ft.Stack(
            controls=[ft.Container(width=fill_w, height=height, bgcolor=color, border_radius=999)],
            height=height,
        ),
    )


def _badge_chip(bid: str) -> ft.Container:
    emoji, label = BADGE_META.get(bid, ("🏅", bid))
    return ft.Container(
        bgcolor=ft.colors.with_opacity(0.10, ft.colors.PRIMARY),
        border_radius=12,
        padding=8,
        content=ft.Row([ft.Text(emoji, size=16), ft.Text(label)], spacing=8, alignment=ft.MainAxisAlignment.START),
    )


def create_profile_view(page: ft.Page, roadmap: Roadmap) -> ft.View:
    p = load_progress()

    # Hlavní statistiky
    avatar = ft.CircleAvatar(
        content=ft.Text("Q", size=28, weight=ft.FontWeight.W_800),
        radius=34,
        bgcolor=ft.colors.BLUE_GREY_700,
    )
    name_block = ft.Column(
        [ft.Text("Quant Learner", size=18, weight=ft.FontWeight.BOLD),
         ft.Text("Sbírej XP a drž si streak 🔥", color=ft.colors.GREY_500)],
        spacing=2
    )

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

    # Odznaky
    badges: List[str] = list(p.get("badges", []))
    badges.sort()
    badges_grid = ft.ResponsiveRow(
        [
            ft.Container(_badge_chip(b), col={"xs": 12, "sm": 6, "md": 4, "lg": 3})
            for b in badges
        ],
        columns=12, spacing=10, run_spacing=10
    )

    # Per-kategorie progress
    per_category_rows: List[ft.Control] = []
    for tr in roadmap.tracks:
        nodes = [n for n in roadmap.nodes if n.track == tr.id]
        # Pydantic model → dict
        prog = category_progress_from_nodes([n.model_dump() for n in nodes])
        row = ft.Row(
            [
                ft.Text(tr.name, width=220),
                _progress_bar(prog["pct"], color=ft.colors.GREEN_ACCENT_700),
                ft.Text(f"{prog['done']}/{prog['total']}  ({prog['pct']}%)", width=140, text_align=ft.TextAlign.RIGHT),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        per_category_rows.append(row)

    body = ft.Column(
        [
            ft.Row([avatar, name_block], spacing=16),
            ft.Divider(opacity=0.1),
            stats,
            ft.Divider(opacity=0.1),
            ft.Text("Odznaky", size=16, weight=ft.FontWeight.BOLD),
            badges_grid if badges else ft.Text("Zatím žádné odznaky — plň lekce a vracej se denně!"),
            ft.Divider(opacity=0.1),
            ft.Text("Postup podle kategorií", size=16, weight=ft.FontWeight.BOLD),
            ft.Column(per_category_rows, spacing=8),
        ],
        spacing=16
    )

    return ft.View(
        route="/profile",
        controls=[
            ft.AppBar(title=ft.Text("Profil"), center_title=True, bgcolor=ft.colors.SURFACE_VARIANT),
            ft.Container(content=body, padding=16)
        ]
    )
