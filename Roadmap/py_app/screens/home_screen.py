import flet as ft

def home_screen(page: ft.Page):
    page.title = "Roadmap – Domů"
    page.scroll = "adaptive"

    def goto_category(e):
        page.go("/category")

    page.add(
        ft.Column(
            [
                ft.Text("📚 Moje studijní roadmapa", size=28, weight="bold"),
                ft.Text("Vyber si kategorii a začni studovat!", size=16, color="grey"),
                ft.ElevatedButton("Matematické základy", on_click=goto_category),
            ],
            horizontal_alignment="center",
            spacing=20,
        )
    )
