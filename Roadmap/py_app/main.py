# py_app/main.py
import flet as ft
from pathlib import Path
from py_app.app import main

if __name__ == "__main__":
    ASSETS = Path(__file__).resolve().parent / "assets"
    ft.app(target=main, assets_dir=str(ASSETS))
