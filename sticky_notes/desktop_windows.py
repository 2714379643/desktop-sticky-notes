"""窗口置底处理。

Qt 在 Windows 上仅对无边框或全屏窗口支持 WindowStaysOnBottomHint；
主窗口已经是无边框窗口。此模块仍需在用户的 Windows 电脑上实机验收。
"""

import ctypes
import sys

from PySide6.QtCore import QTimer, Qt


def apply_bottom_layer(window, enabled=True):
    """开启或关闭“位于普通应用下方”的窗口提示。"""
    bottom_flag = Qt.WindowType.WindowStaysOnBottomHint
    currently_enabled = bool(window.windowFlags() & bottom_flag)
    was_visible = window.isVisible()

    if currently_enabled != enabled:
        window.setWindowFlag(bottom_flag, enabled)
        if was_visible:
            window.show()

    if enabled and sys.platform == "win32":
        QTimer.singleShot(0, lambda: _send_to_bottom(window))


def _send_to_bottom(window):
    """在 Windows 上再发送一次 HWND_BOTTOM，增强置底效果。"""
    if sys.platform != "win32":
        return

    try:
        hwnd_bottom = 1
        swp_nosize = 0x0001
        swp_nomove = 0x0002
        swp_noactivate = 0x0010
        ctypes.windll.user32.SetWindowPos(
            int(window.winId()),
            hwnd_bottom,
            0,
            0,
            0,
            0,
            swp_nosize | swp_nomove | swp_noactivate,
        )
    except (AttributeError, OSError, TypeError, ValueError):
        # Qt 的 WindowStaysOnBottomHint 仍然保留，原生增强失败不让程序退出。
        pass
