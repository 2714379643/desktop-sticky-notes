"""窗口置底处理。

Qt 在 Windows 上仅对无边框或全屏窗口支持 WindowStaysOnBottomHint；
主窗口已经是无边框窗口。此模块仍需在用户的 Windows 电脑上实机验收。
"""

import ctypes
import sys

from PySide6.QtCore import Qt, QTimer


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("accent_state", ctypes.c_int),
        ("accent_flags", ctypes.c_int),
        ("gradient_color", ctypes.c_uint),
        ("animation_id", ctypes.c_int),
    ]


class _WindowCompositionAttributeData(ctypes.Structure):
    _fields_ = [
        ("attribute", ctypes.c_int),
        ("data", ctypes.c_void_p),
        ("size_of_data", ctypes.c_size_t),
    ]


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


def apply_glass_backdrop(window, enabled=True, tint=None):
    """Windows 上启用主题化亚克力模糊；其他平台使用透明绘制。"""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        # Windows 11 的系统级圆角；旧版 Windows 不支持时会自动忽略。
        corner_preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            33,  # DWMWA_WINDOW_CORNER_PREFERENCE
            ctypes.byref(corner_preference),
            ctypes.sizeof(corner_preference),
        )

        # ACCENT_ENABLE_ACRYLICBLURBEHIND / ACCENT_DISABLED
        state = 4 if enabled else 0
        # Windows 使用 AABBGGRR。不同主题只改变轻薄色调，仍保留桌面透景。
        red, green, blue, alpha = tint or (232, 236, 236, 40)
        red = max(0, min(int(red), 255))
        green = max(0, min(int(green), 255))
        blue = max(0, min(int(blue), 255))
        alpha = max(0, min(int(alpha), 255))
        gradient = (
            (alpha << 24) | (blue << 16) | (green << 8) | red
            if enabled
            else 0
        )
        policy = _AccentPolicy(state, 2, gradient, 0)
        data = _WindowCompositionAttributeData(
            19,
            ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p),
            ctypes.sizeof(policy),
        )
        setter = ctypes.windll.user32.SetWindowCompositionAttribute
        setter(hwnd, ctypes.byref(data))
    except (AttributeError, OSError, TypeError, ValueError):
        pass
