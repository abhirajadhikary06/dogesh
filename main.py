"""
Dogesh Assistant – Entry Point
Run: flet run main.py
"""

import sys
import os

# ── Ensure project root is on the path ───────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft
from ui.flet_ui import main_app


def main(page: ft.Page):
    main_app(page)


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",
    )
