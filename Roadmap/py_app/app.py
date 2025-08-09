import flet as ft
from core.utils import load_roadmap
from screens.category_screen import create_category_screen
from screens.home_screen import create_home_view
from screens.profile_screen import create_profile_view
from screens.settings_screen import create_settings_view

ROADMAP_PATH = "core/data/roadmap.json"


def main(page: ft.Page):
    page.title = "WannabeQuant Roadmap"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1100
    page.window_height = 740
    page.scroll = ft.ScrollMode.AUTO

    # — data —
    roadmap = load_roadmap(ROADMAP_PATH)

    # ===== Views (sekce) =====
    def render_home_view() -> ft.View:
        return create_home_view(page, roadmap)

    def render_categories_view() -> ft.View:
        tiles = []
        for tr in roadmap.tracks:
            cnt = sum(1 for n in roadmap.nodes if n.track == tr.id)
            tiles.append(
                ft.ListTile(
                    leading=ft.CircleAvatar(bgcolor=ft.colors.BLUE_GREY_800, content=ft.Text("📘")),
                    title=ft.Text(tr.name, weight=ft.FontWeight.W_700),
                    subtitle=ft.Text(f"{cnt} lekcí"),
                    trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                    on_click=lambda e, cid=tr.id, cname=tr.name: open_category(cid, cname),
                )
            )
        body = ft.Column(tiles, spacing=6, expand=True, scroll=ft.ScrollMode.AUTO, height=page.height-140)

        return ft.View(
            route="/categories",
            controls=[
                ft.AppBar(title=ft.Text("Kategorie"), center_title=True, bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Container(content=body, padding=12, expand=False),
            ],
            vertical_alignment=ft.MainAxisAlignment.START,
        )

    def render_profile_view() -> ft.View:
        return create_profile_view(page, roadmap)

    def render_settings_view() -> ft.View:
        return create_settings_view(page)

    # ===== Navigace mezi sekcemi =====
    def set_tab(index: int):
        page.views.clear()
        if index == 0:
            page.views.append(render_home_view())
        elif index == 1:
            page.views.append(render_categories_view())
        elif index == 2:
            page.views.append(render_profile_view())
        elif index == 3:
            page.views.append(render_settings_view())
        page.update()

    def on_nav_change(e: ft.ControlEvent):
        set_tab(e.control.selected_index)

    # ===== Kategorie detail (stack) =====
    def go_back(e=None):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    def open_category(category_id: str, category_name: str):
        page.views.append(create_category_screen(page, category_id, category_name, on_back=go_back))
        page.update()

    # ===== Bottom Navigation bar =====
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="Domů"),
            ft.NavigationDestination(icon=ft.icons.CATEGORY_OUTLINED, selected_icon=ft.icons.CATEGORY, label="Kategorie"),
            ft.NavigationDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="Profil"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="Nastavení"),
        ],
        on_change=on_nav_change,
        selected_index=0,
        bgcolor=ft.colors.SURFACE_VARIANT,
        elevation=8,
        indicator_color=ft.colors.PRIMARY_CONTAINER,
        height=70,
        label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED,
    )

    # start na „Domů“
    set_tab(0)


ft.app(target=main)
