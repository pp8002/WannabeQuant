from __future__ import annotations
import flet as ft

from py_app.core.models import Roadmap
from py_app.core.progress import get_today_progress, get_current_streak
from py_app.ui.appbar import build_appbar

COLORS = getattr(ft, "colors", getattr(ft, "Colors", None))


def _build_progress_section() -> ft.Row:
    today_progress = get_today_progress()  # float 0.0–1.0
    streak_days = get_current_streak()     # int

    # Daily Goal
    daily_goal = ft.Container(
        bgcolor=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[COLORS.DEEP_PURPLE, COLORS.INDIGO],
        ),
        border_radius=16,
        padding=20,
        expand=True,
        content=ft.Column(
            [
                ft.Text("Daily Goal", color=COLORS.WHITE, size=14),
                ft.Row([
                    ft.ProgressRing(value=today_progress, color=COLORS.WHITE, width=40, height=40),
                    ft.Text(f"{int(today_progress * 5)}/5 lessons", color=COLORS.WHITE),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ElevatedButton("Complete Goal", bgcolor=COLORS.WHITE, color=COLORS.INDIGO),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
    )

    # Streak (zůstává stejné)
    streak = ft.Container(
        bgcolor=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[COLORS.GREEN, COLORS.TEAL],
        ),
        border_radius=16,
        padding=20,
        expand=True,
        content=ft.Column(
            [
                ft.Text("Current Streak", color=COLORS.WHITE, size=14),
                ft.Row([
                    ft.Icon(name=ft.Icons.LOCAL_FIRE_DEPARTMENT, color=COLORS.YELLOW_100),
                    ft.Text(f"{streak_days} days", size=22, weight=ft.FontWeight.BOLD, color=COLORS.WHITE),
                ]),
                ft.Text("Keep it going!", color=COLORS.WHITE),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
    )

    return ft.Row([daily_goal, streak], spacing=16)



def _track_tile(track_id: str, title: str, on_open_category) -> ft.Container:
    return ft.Container(
        bgcolor=COLORS.with_opacity(0.06, COLORS.ON_SURFACE),
        border_radius=12,
        padding=16,
        content=ft.Row(
            [
                ft.Icon(name=ft.Icons.INSIGHTS, color=COLORS.GREY_300),
                ft.Text(title, expand=True, size=18, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    tooltip="Otevřít kategorii",
                    on_click=lambda e: on_open_category(track_id, title),
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    )


def home_screen(page: ft.Page, roadmap: Roadmap, on_open_category) -> ft.View:
    appbar = build_appbar(title=ft.Text("Vítej 👋", size=22, weight=ft.FontWeight.BOLD))
    intro = ft.Text("Vyber si kategorii a začni studovat.", color=COLORS.GREY_400)
    tiles = [_track_tile(track.id, track.name, on_open_category) for track in roadmap.tracks]

    body = ft.Column(
        controls=[
            ft.Container(content=_build_progress_section(), padding=ft.padding.symmetric(vertical=20)),
            intro,
            *tiles
        ],
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
    )

    return ft.View(
        route="/",
        controls=[
            appbar,
            ft.Container(content=body, padding=16, expand=True),
        ]
    )


def create_home_view(page: ft.Page, roadmap: Roadmap, on_open_category):
    return home_screen(page, roadmap, on_open_category)
