"""为无边框弹窗应用与当前主题一致的 Windows 材质。"""

from PySide6.QtCore import QTimer

from sticky_notes.desktop_windows import apply_glass_backdrop
from sticky_notes.themes import THEMES


def schedule_dialog_material(dialog, theme_name):
    colors = THEMES.get(theme_name, THEMES["雾光玻璃"])
    enabled = colors["mode"] == "glass"
    QTimer.singleShot(
        0,
        lambda: apply_glass_backdrop(
            dialog,
            enabled,
            colors.get("backdrop"),
        ),
    )
