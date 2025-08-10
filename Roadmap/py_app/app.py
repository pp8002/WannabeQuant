from __future__ import annotations

import flet as ft
from pathlib import Path

# ----- importy interních částí -----
from py_app.core.utils import load_roadmap, default_roadmap_path
from py_app.screens.home_screen import create_home_view
from py_app.screens.profile_screen import create_profile_view
from py_app.screens.settings_screen import create_settings_view
from py_app.screens.category_screen import create_category_screen

# ========= KONSTANTY =========
COLORS = ft.colors
ASSETS = Path("py_app/assets")
ICON_DIR = ASSETS / "icons"  # např. py_app/assets/icons/book.png


# ✅ OPRAVENÁ funkce: ikonový NavigationBarDestination
def _dest_png(label: str, filename: str) -> ft.NavigationDestination:
    # Flet 0.15.0+ NEPODPORUJE obrázky přímo jako ikony v NavigationBar
    # Použijeme jen text a klasickou ikonu (ne vlastní PNG)
    return ft.NavigationDestination(
        icon=ft.icons.BOOK,  # dočasně statická ikona, dokud nepřidáme Image-based layout
        label=label
    )


def _as_control(view_or_control: ft.Control) -> ft.Control:
    """Převede View na Column, pokud je třeba."""
    if isinstance(view_or_control, ft.View):
        return ft.Column(view_or_control.controls, expand=True, spacing=0)
    return view_or_control


def main(page: ft.Page) -> None:
    # --- Nastavení stránky ---
    page.title = "Quant Roadmap"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_min_width = 900
    page.window_min_height = 600
    page.appbar = None
    page.scroll = ft.ScrollMode.AUTO
    page.update()

    # --- Načtení dat roadmapy ---
    roadmap_path = default_roadmap_path()
    roadmap_model = load_roadmap(roadmap_path)

    selected_index: int = 0
    body = ft.Container(expand=True)

    # ===== FACTORY funkce pro obrazovky =====
    def _home() -> ft.Control:
        return create_home_view(page, roadmap_model, on_open_category=_open_category)

    def _profile() -> ft.Control:
        return create_profile_view(page, roadmap_model)

    def _settings() -> ft.Control:
        return create_settings_view(page)

    def _open_category(category_id: str, category_name: str) -> None:
        def _back():
            _show(0)

        view = create_category_screen(page, category_id, category_name, on_back=_back)
        body.content = _as_control(view)
        page.update()

    def _show(idx: int) -> None:
        nonlocal selected_index
        selected_index = idx

        if idx == 0:
            view = _home()
        elif idx == 1:
            view = _profile()
        else:
            view = _settings()

        body.content = _as_control(view)
        nav.selected_index = selected_index
        page.update()

    # ✅ Navigation bar
    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.BOOK, label="Domů"),
            ft.NavigationDestination(icon=ft.icons.STAR, label="Profil"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS, label="Nastavení"),
        ],
        on_change=lambda e: _show(e.control.selected_index),
        height=64,
        bgcolor=ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE),
    )

    page.add(body, nav)
    _show(0)
