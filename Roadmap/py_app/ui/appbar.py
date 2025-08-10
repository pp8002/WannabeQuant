from __future__ import annotations
import flet as ft
from typing import Optional, Tuple

from py_app.core.progress import load_progress

# Kompatibilita napříč verzemi Fletu (někde je "colors", jinde "Colors")
COLORS = getattr(ft, "colors", getattr(ft, "Colors", None))  # type: ignore

AVATAR_EMOJI = "🧠"


def _xp_level_state() -> Tuple[int, int, int]:
    p = load_progress()
    xp = int(p.get("xp", 0))
    level = xp // 100 + 1
    xp_in_level = xp % 100
    return level, xp_in_level, 100


def _badges_count() -> int:
    return len(load_progress().get("badges", []))


def _streak_days() -> int:
    return int(load_progress().get("streak_days", 0))


def _xp_bar(width_px: int = 120) -> ft.Stack:
    level, cur, total = _xp_level_state()
    pct = 0 if total <= 0 else cur / total
    bg = ft.Container(
        width=width_px, height=8,
        bgcolor=COLORS.with_opacity(0.14, COLORS.PRIMARY),
        border_radius=999,
    )
    fg = ft.Container(
        width=int(width_px * pct), height=8,
        bgcolor=COLORS.AMBER, border_radius=999,
    )
    return ft.Stack([bg, fg])


def build_appbar(
    title: Optional[ft.Control] = None,
    leading: Optional[ft.Control] = None,
    extra_left: Optional[ft.Control] = None,
    extra_actions: Optional[list[ft.Control]] = None,
) -> ft.Container:
    """
    Vizuální "appbar" postavený z běžných kontejnerů (žádný ft.AppBar),
    aby fungoval i na starších verzích Fletu.
    """
    level, cur, total = _xp_level_state()
    badges = _badges_count()
    streak = _streak_days()

    # Avatar
    avatar = ft.Container(
        content=ft.Text(AVATAR_EMOJI, size=22),
        width=34, height=34,
        bgcolor=COLORS.with_opacity(0.08, COLORS.PRIMARY),
        border_radius=999,
        alignment=ft.alignment.center,
    )

    # XP blok
    xp_block = ft.Column(
        [
            ft.Row(
                [
                    ft.Text(f"Lv {level}", size=12, weight=ft.FontWeight.W_700),
                    ft.Text(f"{cur}/{total} XP", size=11, color=COLORS.GREY_600),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            _xp_bar(120),
        ],
        spacing=4,
    )

    # Jednoduché "chips" místo Badge
    def chip(text: str, color):
        return ft.Container(
            padding=ft.padding.symmetric(8, 6),
            border_radius=999,
            bgcolor=COLORS.with_opacity(0.08, color),
            content=ft.Text(text, size=12, weight=ft.FontWeight.W_600),
        )

    right_profile = ft.Row(
        [
            chip(f"🏅 {badges}", COLORS.BLUE),
            chip(f"🔥 {streak}", COLORS.AMBER),
            ft.Container(width=4),
            avatar,
        ] + ([] if not extra_actions else [ft.Container(width=8)] + list(extra_actions)),
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Levá část: leading (např. zpět) + title (+ extra_left pod ním)
    title_ctrl = title if title is not None else ft.Text("")
    if extra_left is not None:
        title_ctrl = ft.Column([title_ctrl, extra_left], spacing=4)

    left_side = ft.Row(
        [leading] + [title_ctrl] if leading else [title_ctrl],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Vlastní horní pruh
    bar = ft.Container(
        bgcolor=getattr(COLORS, "SURFACE_VARIANT", COLORS.with_opacity(0.06, COLORS.ON_SURFACE)),
        padding=ft.padding.symmetric(16, 10),
        content=ft.Row(
            [
                left_side,
                ft.Container(expand=True),  # pružná mezera
                xp_block,
                ft.Container(width=12),
                right_profile,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return bar
