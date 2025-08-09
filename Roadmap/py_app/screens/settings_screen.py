# screens/settings_screen.py
import flet as ft
from core.progress import get_daily_goal, set_daily_goal

def create_settings_view(page: ft.Page) -> ft.View:
    goal_val = get_daily_goal()
    slider = ft.Slider(min=0, max=200, divisions=20, value=goal_val, label="{value} XP")
    input_field = ft.TextField(label="Denní cíl (XP)", value=str(goal_val), width=160)

    def on_slider_change(e):
        v = int(slider.value)
        input_field.value = str(v)
        set_daily_goal(v)
        page.snack_bar = ft.SnackBar(ft.Text(f"Denní cíl nastaven na {v} XP"), open=True)
        page.update()

    def on_input_submit(e):
        try:
            v = int(input_field.value)
        except Exception:
            v = goal_val
        v = max(0, min(5000, v))
        slider.value = min(v, 200)
        set_daily_goal(v)
        page.snack_bar = ft.SnackBar(ft.Text(f"Denní cíl nastaven na {v} XP"), open=True)
        page.update()

    slider.on_change = on_slider_change
    input_field.on_submit = on_input_submit

    theme_switch = ft.Switch(label="Tmavý režim", value=True)

    def on_theme_change(e):
        page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        page.update()

    theme_switch.on_change = on_theme_change

    return ft.View(
        route="/settings",
        controls=[
            ft.AppBar(title=ft.Text("Nastavení"), center_title=True, bgcolor=ft.colors.SURFACE_VARIANT),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Denní cíl", size=16, weight=ft.FontWeight.W_700),
                        ft.Row([slider, input_field], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(opacity=0.1),
                        theme_switch,
                    ],
                    spacing=16
                ),
                padding=16
            )
        ]
    )
