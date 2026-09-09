"""v1.1 主窗口：玻璃便签、连续任务列表、底部语录与日期切换。"""

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from sticky_notes.calendar_utils import normalize_calendar_date
from sticky_notes.task_service import TaskService
from sticky_notes.themes import (
    THEMES,
    compact_calendar_style,
    dialog_style,
    note_style,
)
from sticky_notes.ui.month_calendar import CompactMonthCalendar
from sticky_notes.ui.dialog_material import schedule_dialog_material
from sticky_notes.ui.controls import CircleButton
from sticky_notes.ui.task_dialog import TaskDialog
from sticky_notes.quotes.daily_quote import get_daily_quote

WINDOW_RATIO = 490 / 710
REPEAT_TEXT = {"daily": "每天", "weekly": "每周", "monthly": "每月"}

class NoteSurface(QFrame):
    """绘制主题化的圆角表面；只有雾光主题叠加玻璃高光。"""

    def __init__(self, theme_name, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.setObjectName("paper")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        asset = Path(__file__).resolve().parents[1] / "assets" / "elaina_vignette.png"
        self._elaina_art = QPixmap(str(asset)) if asset.is_file() else QPixmap()

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        colors = THEMES.get(self.theme_name, THEMES["雾光玻璃"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.2, 1.2, -1.2, -1.2)
        path = QPainterPath()
        path.addRoundedRect(rect, 34, 34)

        self._paint_surface(painter, rect, path, colors)
        self._paint_texture(painter, rect, path, colors)

        border = QColor(*colors["edge"])
        painter.setPen(QPen(border, 1.35 if colors.get("mode") == "glass" else 1.05))
        painter.drawPath(path)

        if colors.get("mode") == "glass":
            # 三道轻重不同的边缘，让窗口像有厚度的圆角玻璃，而不是透明色块。
            inner = QRectF(rect).adjusted(3.0, 3.0, -3.0, -3.0)
            inner_path = QPainterPath()
            inner_path.addRoundedRect(inner, 30, 30)
            painter.setPen(QPen(QColor(255, 255, 255, 132), 0.75))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(inner_path)

            bottom_edge = QPainterPath()
            bottom_edge.moveTo(rect.left() + 40, rect.bottom() - 2.5)
            bottom_edge.cubicTo(
                rect.center().x() - 80,
                rect.bottom() + 0.3,
                rect.center().x() + 80,
                rect.bottom() + 0.3,
                rect.right() - 40,
                rect.bottom() - 2.5,
            )
            painter.setPen(QPen(QColor(91, 131, 168, 72), 2.0))
            painter.drawPath(bottom_edge)

        if self.theme_name == "伊蕾娜旅记" and not self._elaina_art.isNull():
            painter.save()
            painter.setClipPath(path)
            painter.setOpacity(0.20)
            target = QRectF(
                rect.left() + rect.width() * 0.29,
                rect.top() + rect.height() * 0.36,
                rect.width() * 0.73,
                rect.height() * 0.63,
            )
            painter.drawPixmap(target, self._elaina_art, QRectF(self._elaina_art.rect()))
            painter.restore()

        self._paint_motif(painter, rect, path, colors)
        painter.end()
        super().paintEvent(event)

    @staticmethod
    def _paint_surface(painter, rect, clip_path, colors):
        red, green, blue, alpha = colors["surface"]
        motif = colors.get("motif", "none")
        if colors.get("mode") == "glass":
            base = QLinearGradient(rect.topLeft(), rect.bottomRight())
            base.setColorAt(0.0, QColor(244, 251, 255, 76))
            base.setColorAt(0.34, QColor(red, green, blue, alpha))
            base.setColorAt(0.76, QColor(199, 222, 236, 28))
            base.setColorAt(1.0, QColor(238, 248, 252, 52))
            painter.fillPath(clip_path, QBrush(base))

            gleam = QRadialGradient(
                QPointF(rect.left() + rect.width() * 0.18, rect.top() + rect.height() * 0.08),
                rect.width() * 0.72,
            )
            gleam.setColorAt(0.0, QColor(255, 255, 255, 105))
            gleam.setColorAt(0.45, QColor(255, 255, 255, 24))
            gleam.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillPath(clip_path, QBrush(gleam))
            return

        if motif == "clouds":
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(255, 240, 247))
            gradient.setColorAt(0.48, QColor(251, 226, 238))
            gradient.setColorAt(1.0, QColor(244, 225, 248))
            painter.fillPath(clip_path, QBrush(gradient))
        elif motif == "night":
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(18, 21, 24))
            gradient.setColorAt(0.55, QColor(24, 27, 31))
            gradient.setColorAt(1.0, QColor(16, 19, 22))
            painter.fillPath(clip_path, QBrush(gradient))
        elif motif == "elaina":
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(35, 30, 53))
            gradient.setColorAt(0.56, QColor(48, 41, 67))
            gradient.setColorAt(1.0, QColor(27, 24, 44))
            painter.fillPath(clip_path, QBrush(gradient))
        else:
            painter.fillPath(clip_path, QColor(red, green, blue, alpha))

    @staticmethod
    def _paint_texture(painter, rect, clip_path, colors):
        """用固定坐标绘制轻纸纤维；每次刷新图案稳定，不会出现闪动。"""
        motif = colors.get("motif", "none")
        if motif not in {"branch", "ink", "forest"}:
            return
        painter.save()
        painter.setClipPath(clip_path)
        texture = QColor(colors["text"])
        texture.setAlpha(10 if motif != "forest" else 8)
        painter.setPen(QPen(texture, 0.55))
        width = max(1, int(rect.width()))
        height = max(1, int(rect.height()))
        for index in range(92):
            x = rect.left() + ((index * 71 + 19) % width)
            y = rect.top() + ((index * 113 + 31) % height)
            length = 3 + (index * 5) % 9
            rise = ((index % 5) - 2) * 0.7
            painter.drawLine(QPointF(x, y), QPointF(x + length, y + rise))
        painter.restore()

    @staticmethod
    def _paint_motif(painter, rect, clip_path, colors):
        motif = colors.get("motif", "none")
        if motif == "none":
            return

        painter.save()
        painter.setClipPath(clip_path)
        ink = QColor(colors["accent"])

        if motif == "branch":
            # 左上松枝、飘落花瓣、底部远山和朱印，位置对应日式庭院概念稿。
            trunk = QColor("#384638")
            trunk.setAlpha(178)
            painter.setPen(QPen(trunk, 2.4))
            pine = QPainterPath()
            pine.moveTo(rect.left() - 3, rect.top() + 88)
            pine.cubicTo(rect.left() + 16, rect.top() + 59, rect.left() + 15, rect.top() + 26, rect.left() + 39, rect.top() - 2)
            painter.drawPath(pine)
            for ox, oy, direction in ((12, 45, 1), (18, 29, 1), (28, 16, 1), (5, 68, 1), (38, 11, 1)):
                start = QPointF(rect.left() + ox, rect.top() + oy)
                painter.setPen(QPen(trunk, 1.05))
                painter.drawLine(start, QPointF(start.x() + 52 * direction, start.y() - 10))
                needle = QColor("#36533d")
                needle.setAlpha(145)
                painter.setPen(QPen(needle, 0.85))
                for step in range(6):
                    px = start.x() + 11 + step * 7
                    py = start.y() - 2 - step * 1.3
                    painter.drawLine(QPointF(px, py), QPointF(px - 4, py - 11))
                    painter.drawLine(QPointF(px, py), QPointF(px + 5, py - 9))

            mountain = QColor("#4e5a46")
            mountain.setAlpha(42)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(mountain)
            ridge = QPainterPath()
            ridge.moveTo(rect.left() - 8, rect.bottom() - 25)
            ridge.lineTo(rect.left() + 38, rect.bottom() - 112)
            ridge.lineTo(rect.left() + 72, rect.bottom() - 65)
            ridge.lineTo(rect.left() + 115, rect.bottom() - 123)
            ridge.lineTo(rect.left() + 161, rect.bottom() - 39)
            ridge.lineTo(rect.left() + 190, rect.bottom() - 19)
            ridge.closeSubpath()
            painter.drawPath(ridge)

            petal = QColor("#c9443d")
            petal.setAlpha(200)
            painter.setBrush(petal)
            for x, y, rx, ry in ((0.43, 0.06, 5, 9), (0.05, 0.78, 4, 8), (0.88, 0.74, 4, 8), (0.34, 0.88, 5, 9), (0.76, 0.89, 5, 8)):
                painter.drawEllipse(QPointF(rect.left() + rect.width() * x, rect.top() + rect.height() * y), rx, ry)

            seal_rect = QRectF(rect.right() - 58, rect.bottom() - 148, 30, 42)
            painter.setBrush(QColor("#b8322c"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(seal_rect, 3, 3)
            painter.setPen(QColor(255, 247, 225, 235))
            seal_font = painter.font()
            seal_font.setPixelSize(20)
            seal_font.setBold(True)
            painter.setFont(seal_font)
            painter.drawText(seal_rect, Qt.AlignmentFlag.AlignCenter, "静")

        elif motif == "ink":
            # 右上竹叶和底部横向水墨山景。
            bamboo = QColor("#46534e")
            bamboo.setAlpha(138)
            painter.setPen(QPen(bamboo, 2.0))
            painter.drawLine(QPointF(rect.right() - 8, rect.top() - 6), QPointF(rect.right() - 66, rect.top() + 126))
            painter.setBrush(bamboo)
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y, angle in ((-22, 23, -1), (-31, 43, 1), (-43, 59, -1), (-51, 80, 1), (-60, 97, -1), (-70, 113, 1)):
                leaf = QPainterPath()
                cx, cy = rect.right() + x, rect.top() + y
                leaf.moveTo(cx, cy)
                leaf.cubicTo(cx + 17 * angle, cy - 10, cx + 27 * angle, cy + 1, cx + 4 * angle, cy + 9)
                leaf.closeSubpath()
                painter.drawPath(leaf)

            for layer, alpha in ((0, 30), (1, 46), (2, 68)):
                shade = QColor("#4c5b57")
                shade.setAlpha(alpha)
                painter.setBrush(shade)
                ridge = QPainterPath()
                base = rect.bottom() - 20 + layer * 9
                ridge.moveTo(rect.left() - 10, base)
                points = ((0.04, -40), (0.13, -76), (0.22, -34), (0.36, -62), (0.50, -28), (0.68, -94), (0.78, -46), (0.90, -119), (1.04, -31))
                for ratio, rise in points:
                    ridge.lineTo(rect.left() + rect.width() * ratio, base + rise + layer * 7)
                ridge.lineTo(rect.right() + 10, rect.bottom() + 4)
                ridge.lineTo(rect.left() - 10, rect.bottom() + 4)
                ridge.closeSubpath()
                painter.drawPath(ridge)
            painter.setPen(QPen(QColor(42, 55, 52, 125), 1.0))
            for bx, by in ((0.72, 0.76), (0.76, 0.74), (0.80, 0.77)):
                x = rect.left() + rect.width() * bx
                y = rect.top() + rect.height() * by
                painter.drawLine(QPointF(x - 5, y), QPointF(x, y + 3))
                painter.drawLine(QPointF(x, y + 3), QPointF(x + 5, y))

        elif motif == "forest":
            leaf = QColor("#31553d")
            leaf.setAlpha(152)
            for start_x, start_y, direction in ((rect.right() + 5, rect.top() + 22, -1), (rect.left() - 8, rect.bottom() - 48, 1), (rect.right() + 8, rect.bottom() - 36, -1)):
                painter.setPen(QPen(leaf, 1.5))
                painter.drawLine(QPointF(start_x, start_y), QPointF(start_x + 100 * direction, start_y + (74 if start_y < rect.center().y() else -70)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(leaf)
                for step in range(7):
                    x = start_x + (15 + step * 12) * direction
                    y = start_y + (10 + step * 9) * (1 if start_y < rect.center().y() else -1)
                    painter.drawEllipse(QPointF(x, y), 11, 3.5)
                    painter.drawEllipse(QPointF(x - 7 * direction, y + 8), 10, 3.2)
            berries = QColor("#c79a35")
            berries.setAlpha(215)
            painter.setBrush(berries)
            for x, y in ((0.15, 0.82), (0.18, 0.80), (0.20, 0.84), (0.23, 0.81)):
                painter.drawEllipse(QPointF(rect.left() + rect.width() * x, rect.top() + rect.height() * y), 4.5, 5.5)
            dash = QColor("#2f5e45")
            dash.setAlpha(170)
            painter.setPen(QPen(dash, 1.4, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(rect.left() + 20, rect.top() + 24), QPointF(rect.left() + 20, rect.top() + 110))
            painter.drawLine(QPointF(rect.right() - 20, rect.bottom() - 116), QPointF(rect.right() - 20, rect.bottom() - 34))

        elif motif == "night":
            gold = QColor("#d8b56f")
            gold.setAlpha(168)
            painter.setPen(QPen(gold, 0.9))
            groups = (
                ((0.01, 0.10), (0.08, 0.06), (0.17, 0.09), (0.28, 0.035)),
                ((0.00, 0.84), (0.09, 0.79), (0.18, 0.91), (0.30, 0.86)),
                ((0.72, 0.89), (0.82, 0.84), (0.93, 0.88), (1.01, 0.81)),
            )
            painter.setBrush(gold)
            for points in groups:
                mapped = [QPointF(rect.left() + rect.width() * x, rect.top() + rect.height() * y) for x, y in points]
                for first, second in zip(mapped, mapped[1:]):
                    painter.drawLine(first, second)
                for point in mapped:
                    painter.drawEllipse(point, 2.0, 2.0)
            for x, y, size in ((0.05, 0.12, 8), (0.12, 0.05, 5), (0.87, 0.87, 8), (0.76, 0.91, 4)):
                cx = rect.left() + rect.width() * x
                cy = rect.top() + rect.height() * y
                painter.drawLine(QPointF(cx - size, cy), QPointF(cx + size, cy))
                painter.drawLine(QPointF(cx, cy - size), QPointF(cx, cy + size))
            # 月相沿右上排列。
            for index, phase in enumerate((0.24, 0.47, 0.72, 1.0)):
                center = QPointF(rect.right() - 126 + index * 27, rect.top() + 32)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(216, 181, 111, 205))
                painter.drawEllipse(center, 7.5, 7.5)
                if phase < 1.0:
                    painter.setBrush(QColor(18, 21, 24))
                    painter.drawEllipse(QPointF(center.x() - 8 * (1 - phase), center.y()), 7.6, 7.6)

        elif motif == "clouds":
            painter.setPen(Qt.PenStyle.NoPen)
            for base_y, cloud_color, points in (
                (rect.bottom() - 35, QColor(230, 190, 239, 145), ((18, 42), (75, 63), (145, 45), (rect.width() - 60, 72))),
                (rect.bottom() - 16, QColor(255, 228, 238, 225), ((-6, 40), (54, 48), (rect.width() - 122, 57), (rect.width() - 42, 72))),
            ):
                painter.setBrush(cloud_color)
                for x, radius in points:
                    painter.drawEllipse(QPointF(rect.left() + x, base_y), radius, radius * 0.58)
            sun_center = QPointF(rect.right() - 55, rect.top() + 58)
            sun_glow = QRadialGradient(sun_center, 52)
            sun_glow.setColorAt(0, QColor(255, 183, 137, 225))
            sun_glow.setColorAt(0.55, QColor(255, 211, 174, 105))
            sun_glow.setColorAt(1, QColor(255, 220, 190, 0))
            painter.setBrush(QBrush(sun_glow))
            painter.drawEllipse(sun_center, 52, 52)
            painter.setBrush(QColor(255, 181, 137, 220))
            painter.drawEllipse(sun_center, 20, 20)

        elif motif == "swiss":
            red = QColor("#ed302b")
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(red)
            painter.drawRect(QRectF(rect.left() + 24, rect.top() + 26, 12, 12))
            painter.drawRect(QRectF(rect.right() - 37, rect.top() + 26, 12, 12))
            painter.drawRect(QRectF(rect.left() + 24, rect.bottom() - 86, 12, 12))
            painter.setPen(QPen(QColor(20, 23, 25, 190), 1.0))
            painter.drawLine(QPointF(rect.right() - 69, rect.top() + 13), QPointF(rect.right() - 69, rect.top() + 56))
            painter.drawLine(QPointF(rect.left() + 52, rect.bottom() - 79), QPointF(rect.right() - 25, rect.bottom() - 79))

        elif motif == "elaina":
            ink.setAlpha(78)
            painter.setPen(QPen(ink, 0.9))
            points = ((0.10, 0.13), (0.18, 0.10), (0.25, 0.16), (0.32, 0.11))
            mapped = [QPointF(rect.left() + rect.width() * x, rect.top() + rect.height() * y) for x, y in points]
            for first, second in zip(mapped, mapped[1:]):
                painter.drawLine(first, second)
            painter.setBrush(ink)
            painter.setPen(Qt.PenStyle.NoPen)
            for point in mapped:
                painter.drawEllipse(point, 1.8, 1.8)

            crescent = QPointF(rect.right() - 52, rect.top() + 61)
            painter.setBrush(QColor(230, 213, 248, 195))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(crescent, 20, 20)
            painter.setBrush(QColor(43, 38, 61))
            painter.drawEllipse(QPointF(crescent.x() + 8, crescent.y() - 5), 20, 20)

        painter.restore()


class DragStrip(QWidget):
    """无边框窗口的拖动区域。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("按住这里拖动便签")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class SlidersButton(CircleButton):
    """用绘制的滑杆代替字体不统一的齿轮图标。"""

    def __init__(self, theme_name="雾光玻璃", parent=None):
        super().__init__("", theme_name, parent)
        self.setAccessibleName("设置")
        self.setToolTip("设置、导入与备份")

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(THEMES.get(self.theme_name, THEMES["雾光玻璃"])["text"])
        pen = QPen(color, 1.55)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        left, right = self.width() * 0.27, self.width() * 0.73
        positions = ((0.34, 0.45), (0.50, 0.65), (0.66, 0.38))
        for y_ratio, knob_ratio in positions:
            y = self.height() * y_ratio
            painter.drawLine(QPointF(left, y), QPointF(right, y))
            painter.setBrush(color)
            painter.drawEllipse(QPoint(int(self.width() * knob_ratio), int(y)), 2, 2)
        painter.end()


class RoundAddButton(QPushButton):
    """直接绘制正圆，避免不同 Windows 样式把按钮显示成方形。"""

    def __init__(self, theme_name, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.setObjectName("roundAddButton")
        self.setAccessibleName("添加任务")
        self.setToolTip("添加任务")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        colors = THEMES.get(self.theme_name, THEMES["雾光玻璃"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isEnabled():
            fill_key = "accent_hover" if self.underMouse() else "accent"
            fill = QColor(colors[fill_key])
            plus = QColor(colors.get("accent_text", "white"))
        else:
            fill = QColor(colors["muted"])
            fill.setAlpha(52)
            plus = QColor(colors["muted"])

        inset = 3.5 if self.isDown() else 2.2
        circle = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        edge = QColor(*colors["edge"])
        edge.setAlpha(min(210, max(105, edge.alpha())))

        shadow = QColor(colors["shadow"][0], colors["shadow"][1], colors["shadow"][2], 78)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawEllipse(circle.translated(0, 2.2))

        if colors.get("motif") == "swiss":
            brush = QBrush(fill)
        else:
            glow = QRadialGradient(
                QPointF(circle.left() + circle.width() * 0.32, circle.top() + circle.height() * 0.26),
                circle.width() * 0.74,
            )
            glow.setColorAt(0.0, fill.lighter(132))
            glow.setColorAt(0.58, fill)
            glow.setColorAt(1.0, fill.darker(125))
            brush = QBrush(glow)
        painter.setPen(QPen(edge, 1.1))
        painter.setBrush(brush)
        painter.drawEllipse(circle)

        highlight = QPainterPath()
        highlight.arcMoveTo(circle.adjusted(3, 3, -3, -3), 42)
        highlight.arcTo(circle.adjusted(3, 3, -3, -3), 42, 96)
        painter.setPen(QPen(QColor(255, 255, 255, 105), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(highlight)

        center = circle.center()
        arm = max(5.0, circle.width() * 0.19)
        pen = QPen(plus, max(1.9, circle.width() * 0.057))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(center.x() - arm, center.y()),
            QPointF(center.x() + arm, center.y()),
        )
        painter.drawLine(
            QPointF(center.x(), center.y() - arm),
            QPointF(center.x(), center.y() + arm),
        )
        painter.end()


class AspectResizeGrip(QWidget):
    """右下角等比例缩放手柄。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self._start_global = None
        self._start_size = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.palette().color(self.foregroundRole())
        color.setAlpha(115)
        pen = QPen(color, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for inset in (5, 9, 13):
            painter.drawLine(self.width() - inset, self.height() - 3, self.width() - 3, self.height() - inset)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_global = event.globalPosition()
            self._start_size = self.window().size()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_global is None or self._start_size is None:
            return
        delta = event.globalPosition() - self._start_global
        width_from_x = self._start_size.width() + delta.x()
        width_from_y = (self._start_size.height() + delta.y()) * WINDOW_RATIO
        target_width = width_from_x if abs(delta.x()) >= abs(delta.y()) * WINDOW_RATIO else width_from_y
        target_width = max(392, min(round(target_width), 840))
        self.window().resize(target_width, round(target_width / WINDOW_RATIO))
        event.accept()

    def mouseReleaseEvent(self, event):
        self._start_global = None
        self._start_size = None
        super().mouseReleaseEvent(event)


class TaskCheckBox(QCheckBox):
    def __init__(self, accent, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setFixedSize(25, 25)

    def set_accent(self, accent):
        self.accent = accent
        self.update()

    def hitButton(self, position):
        return self.rect().contains(position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0 if self.isEnabled() else 0.48)
        accent = QColor(self.accent)
        border = accent if self.isChecked() else self.palette().color(self.foregroundRole())
        border.setAlpha(210 if self.isChecked() else 110)
        painter.setPen(QPen(border, 1.35))
        painter.setBrush(accent if self.isChecked() else QColor(255, 255, 255, 85))
        painter.drawEllipse(2, 2, 20, 20)
        if self.isChecked():
            pen = QPen(QColor("white"), 2.15)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(7, 12, 11, 16)
            painter.drawLine(11, 16, 18, 8)


class TaskRow(QFrame):
    toggle_requested = Signal(str, bool)
    menu_requested = Signal(object, object)

    def __init__(self, task, is_past, can_complete, accent, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("taskRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 13, 2, 13)
        layout.setSpacing(12)
        self.checkbox = TaskCheckBox(accent)
        self.checkbox.setAccessibleName(task.title)
        self.checkbox.setChecked(task.completed)
        self.checkbox.setEnabled(can_complete)
        if not can_complete and not is_past:
            self.checkbox.setToolTip("设置中已禁止提前完成未来任务")
        self.checkbox.toggled.connect(lambda checked: self.toggle_requested.emit(task.task_id, checked))
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)

        texts = QVBoxLayout()
        texts.setSpacing(4)
        self.title_label = QLabel(task.title)
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        self.title_label.setWordWrap(True)
        texts.addWidget(self.title_label)
        details = []
        if task.start_time is not None:
            details.append(f"{task.start_time} — {task.end_time}")
        if task.repeat_rule == "weekly":
            weekday = "一二三四五六日"[task.repeat_weekday]
            details.append(f"↻ 每周星期{weekday}")
        elif task.repeat_rule == "monthly":
            details.append(f"↻ 每月 {task.repeat_monthday} 号")
        elif task.repeat_rule != "none":
            details.append(f"↻ {REPEAT_TEXT[task.repeat_rule]}")
        self.detail_label = QLabel("  ·  ".join(details))
        self.detail_label.setObjectName("secondary")
        self.detail_label.setVisible(bool(details))
        texts.addWidget(self.detail_label)
        layout.addLayout(texts, 1)

        if not is_past:
            more = CircleButton("⋯")
            more.set_theme(getattr(self.window(), "theme", "雾光玻璃"))
            more.setAccessibleName(f"{task.title}的更多操作")
            more.clicked.connect(lambda: self.menu_requested.emit(more, task))
            layout.addWidget(more, 0, Qt.AlignmentFlag.AlignTop)
        self.set_completed(task.completed)

    def set_completed(self, completed):
        blocker = self.checkbox.blockSignals(True)
        self.checkbox.setChecked(completed)
        self.checkbox.blockSignals(blocker)
        font = self.title_label.font()
        font.setStrikeOut(completed)
        self.title_label.setFont(font)
        self.title_label.setProperty("completed", completed)
        self.title_label.style().unpolish(self.title_label)
        self.title_label.style().polish(self.title_label)

    def set_accent(self, accent):
        self.checkbox.set_accent(accent)


class CalendarDialog(QDialog):
    """单月紧凑日历；每个日期只显示一行公历数字。"""

    def __init__(self, selected_date, tasks, theme_name="雾光玻璃", parent=None):
        super().__init__(parent)
        self.selected_date = selected_date
        self.setWindowTitle("选择查看日期")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(410, 385)
        self.setMinimumSize(380, 350)
        self.setStyleSheet(
            dialog_style(theme_name) + compact_calendar_style(theme_name)
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        surface = QFrame()
        surface.setObjectName("dialogSurface")
        root.addWidget(surface)
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        month_row = QHBoxLayout()
        previous_button = CircleButton("‹", theme_name)
        next_button = CircleButton("›", theme_name)
        self.month_label = QLabel()
        self.month_label.setObjectName("calendarMonth")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        month_row.addWidget(previous_button)
        month_row.addWidget(self.month_label, 1)
        month_row.addWidget(next_button)
        layout.addLayout(month_row)

        tasks_by_date = {}
        for task in tasks:
            if not task.cancelled:
                tasks_by_date.setdefault(task.task_date, []).append(task)
        completed_dates = {
            task_date
            for task_date, day_tasks in tasks_by_date.items()
            if day_tasks and all(task.completed for task in day_tasks)
        }
        self.calendar = CompactMonthCalendar(selected_date, completed_dates)
        layout.addWidget(self.calendar)
        layout.addStretch()

        footer = QHBoxLayout()
        hint = QLabel("红点表示当日任务已全部完成")
        hint.setObjectName("secondary")
        today_button = QPushButton("今天")
        footer.addWidget(hint, 1)
        footer.addWidget(today_button)
        layout.addLayout(footer)
        previous_button.clicked.connect(self.calendar.show_previous_month)
        next_button.clicked.connect(self.calendar.show_next_month)
        self.calendar.month_changed.connect(self._update_month)
        self.calendar.date_picked.connect(self._pick)
        today_button.clicked.connect(lambda: self._pick(date.today()))
        self._update_month(self.calendar.year, self.calendar.month)
        schedule_dialog_material(self, theme_name)

    def _update_month(self, year, month):
        self.month_label.setText(f"{year}年 {month}月")

    def _pick(self, chosen):
        self.selected_date = normalize_calendar_date(chosen)
        self.accept()


class RecurringDeleteDialog(QDialog):
    """重复任务只提供清晰的两种删除范围。"""

    def __init__(self, task, theme_name, parent=None):
        super().__init__(parent)
        self.scope = "future"
        self.setWindowTitle("删除重复任务")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(430)
        self.setStyleSheet(dialog_style(theme_name))
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        surface = QFrame()
        surface.setObjectName("dialogSurface")
        root.addWidget(surface)
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(25, 22, 25, 22)
        layout.setSpacing(13)
        title_row = QHBoxLayout()
        heading = QLabel("删除重复任务")
        heading.setObjectName("heading")
        close = CircleButton("×", theme_name)
        close.clicked.connect(self.reject)
        title_row.addWidget(heading)
        title_row.addStretch()
        title_row.addWidget(close)
        layout.addLayout(title_row)
        description = QLabel(f"“{task.title}”属于一个重复任务系列，请选择删除范围。")
        description.setObjectName("secondary")
        description.setWordWrap(True)
        layout.addWidget(description)

        section = QFrame()
        section.setObjectName("section")
        choices = QVBoxLayout(section)
        choices.setContentsMargins(16, 14, 16, 14)
        self.all_option = QRadioButton(
            "全部删除\n将删除该任务的所有重复日期。"
        )
        self.future_option = QRadioButton(
            "删除所选日期及以后的任务\n将删除从选中日期开始及之后的所有重复日期。"
        )
        self.all_option.setObjectName("deleteOption")
        self.future_option.setObjectName("deleteOption")
        self.future_option.setChecked(True)
        choices.addWidget(self.all_option)
        choices.addWidget(self.future_option)
        layout.addWidget(section)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        confirm = QPushButton("确认删除")
        confirm.setObjectName("dangerButton")
        buttons.addWidget(cancel)
        buttons.addWidget(confirm)
        layout.addLayout(buttons)
        cancel.clicked.connect(self.reject)
        confirm.clicked.connect(self._confirm)
        schedule_dialog_material(self, theme_name)

    def _confirm(self):
        self.scope = "all" if self.all_option.isChecked() else "future"
        self.accept()


class NoteWindow(QWidget):
    tasks_changed = Signal()
    settings_requested = Signal()
    modal_state_changed = Signal(bool)
    geometry_changed = Signal()
    close_requested = Signal()

    def __init__(self, task_service, settings=None, parent=None):
        super().__init__(parent)
        if not isinstance(task_service, TaskService):
            raise TypeError("task_service 必须是 TaskService 对象")
        self.task_service = task_service
        self.settings = dict(settings or {})
        self.selected_date = date.today()
        self.theme = self.settings.get("theme", "雾光玻璃")
        if self.theme not in THEMES:
            self.theme = "雾光玻璃"
        self.font_size = max(12, min(int(self.settings.get("font_size", 15)), 22))
        self.allow_early_completion = self.settings.get(
            "allow_early_completion",
            True,
        )
        # 文案与当前查看日期使用同一个日期来源，切换任务日期时同步换句。
        self._quote_date = self.selected_date
        self.quote_text = get_daily_quote(self._quote_date)
        self._last_scale = None
        self._initialized = False

        self.setWindowTitle("桌面便签 1.1")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(392, round(392 / WINDOW_RATIO))
        width = self._positive_setting("window_width", 490)
        width = max(392, min(width, 840))
        self.resize(width, round(width / WINDOW_RATIO))
        self._build_ui()
        self.apply_appearance()
        self.refresh_tasks()
        self._initialized = True

    def _positive_setting(self, key, default):
        value = self.settings.get(key, default)
        return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else default

    def _build_ui(self):
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(8, 6, 8, 10)
        self.paper = NoteSurface(self.theme)
        self.paper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        shadow = QGraphicsDropShadowEffect(self.paper)
        shadow.setBlurRadius(27)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(28, 39, 42, 48))
        self.paper.setGraphicsEffect(shadow)
        self.paper_shadow = shadow
        self.outer_layout.addWidget(self.paper)

        self.content_layout = QVBoxLayout(self.paper)
        self.content_layout.setContentsMargins(25, 2, 25, 15)
        self.content_layout.setSpacing(10)
        self.content_layout.addWidget(DragStrip())

        toolbar = QHBoxLayout()
        self.overline = QLabel("DAILY FOCUS")
        self.overline.setObjectName("overline")
        toolbar.addWidget(self.overline)
        toolbar.addStretch()
        self.settings_button = SlidersButton(self.theme)
        self.settings_button.clicked.connect(self.settings_requested.emit)
        close_button = CircleButton("×", self.theme)
        close_button.setAccessibleName("关闭")
        close_button.setToolTip("缩到托盘")
        close_button.clicked.connect(self.close)
        toolbar.addWidget(self.settings_button)
        toolbar.addWidget(close_button)
        self.content_layout.addLayout(toolbar)

        self.heading_label = QLabel()
        self.heading_label.setObjectName("heading")
        self.heading_label.setWordWrap(True)
        self.content_layout.addWidget(self.heading_label)
        self.day_label = QLabel()
        self.day_label.setObjectName("secondary")
        self.day_label.hide()
        header_rule = QFrame()
        header_rule.setObjectName("headerDivider")
        header_rule.setFixedHeight(1)
        self.content_layout.addWidget(header_rule)

        summary = QHBoxLayout()
        self.count_label = QLabel()
        self.percent_label = QLabel()
        self.count_label.setObjectName("secondary")
        self.percent_label.setObjectName("secondary")
        summary.addWidget(self.count_label)
        summary.addStretch()
        summary.addWidget(self.percent_label)
        self.content_layout.addLayout(summary)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        progress_row.addWidget(self.progress_bar, 1)
        # 统一采用 D 版位置：加号固定在进度条右侧，不占用任务区空间。
        self.add_button = RoundAddButton(self.theme)
        self.add_button.clicked.connect(self.open_add_dialog)
        progress_row.addWidget(self.add_button)
        self.content_layout.addLayout(progress_row)

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 3, 0, 3)
        self.task_layout.setSpacing(0)
        self.task_scroll.setWidget(self.task_container)
        self.content_layout.addWidget(self.task_scroll, 1)

        self.quote_panel = QFrame()
        self.quote_panel.setObjectName("quotePanel")
        quote_layout = QVBoxLayout(self.quote_panel)
        quote_layout.setContentsMargins(13, 9, 13, 9)
        self.quote_scroll = QScrollArea()
        self.quote_scroll.setObjectName("quoteScroll")
        self.quote_scroll.setWidgetResizable(True)
        self.quote_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.quote_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.quote_content = QWidget()
        self.quote_content_layout = QVBoxLayout(self.quote_content)
        self.quote_content_layout.setContentsMargins(3, 2, 3, 2)
        self.quote_label = QLabel()
        self.quote_label.setObjectName("quoteText")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setTextFormat(Qt.TextFormat.PlainText)
        self.quote_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.quote_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.quote_content_layout.addWidget(self.quote_label, 1)
        self.quote_scroll.setWidget(self.quote_content)
        quote_layout.addWidget(self.quote_scroll)
        self.content_layout.addWidget(self.quote_panel)

        navigation = QHBoxLayout()
        previous_button = CircleButton("‹", self.theme)
        next_button = CircleButton("›", self.theme)
        self.calendar_button = QPushButton()
        self.calendar_button.setObjectName("glassButton")
        today_button = QPushButton("今天")
        previous_button.clicked.connect(lambda: self.select_date(self.selected_date - timedelta(days=1)))
        next_button.clicked.connect(lambda: self.select_date(self.selected_date + timedelta(days=1)))
        self.calendar_button.clicked.connect(self.open_calendar)
        today_button.clicked.connect(lambda: self.select_date(date.today()))
        navigation.addWidget(previous_button)
        navigation.addWidget(self.calendar_button, 1)
        navigation.addWidget(next_button)
        navigation.addWidget(today_button)
        navigation.addWidget(AspectResizeGrip())
        self.content_layout.addLayout(navigation)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondary")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(17)
        self.content_layout.addWidget(self.status_label)
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status_label.clear)

    def select_date(self, selected_date):
        if not isinstance(selected_date, date):
            raise TypeError("selected_date 必须是 date 对象")
        self.selected_date = selected_date
        self.refresh_tasks()

    def refresh_tasks(self):
        selected = self.selected_date
        self._sync_quote_to_selected_date()
        selected_iso = selected.isoformat()
        generated = self.task_service.ensure_recurring_for_date(selected_iso)
        if generated and self._initialized:
            self.tasks_changed.emit()
        is_past = selected < date.today()
        tasks = self.task_service.get_tasks_by_date(selected_iso)

        self.heading_label.setText(f"{selected.year}.{selected.month}.{selected.day}  To do list")
        weekday = "一二三四五六日"[selected.weekday()]
        scene = "历史记录" if is_past else "今天" if selected == date.today() else "提前安排"
        self.day_label.setText(f"{scene}  ·  星期{weekday}")
        self.calendar_button.setText(f"{selected.year} 年 {selected.month} 月 {selected.day} 日  ▾")
        self._update_summary()
        self.add_button.setEnabled(not is_past)
        self.add_button.setToolTip("历史任务仅查看" if is_past else "添加任务")

        self._clear_rows()
        if not tasks:
            empty = QLabel("这一天没有记录" if is_past else "这一天，还留着空白。")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_layout.addWidget(empty, 1)
        else:
            accent = THEMES[self.theme]["accent"]
            for task in tasks:
                can_complete = not is_past and (
                    self.allow_early_completion or selected <= date.today()
                )
                row = TaskRow(task, is_past, can_complete, accent)
                for button in row.findChildren(CircleButton):
                    button.set_theme(self.theme)
                row.toggle_requested.connect(lambda task_id, checked, current=row: self._toggle_task(current, task_id, checked))
                row.menu_requested.connect(self._show_task_menu)
                self.task_layout.addWidget(row)
        self.task_layout.addStretch()

    def _update_summary(self):
        completed, total, percentage = self.task_service.completion_for_date(self.selected_date.isoformat())
        self.count_label.setText(f"已完成 {completed} / {total} 项")
        self.percent_label.setText(f"{percentage}%" if total else "暂无任务")
        self.progress_bar.setValue(percentage)

    def _clear_rows(self):
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _toggle_task(self, row, task_id, checked):
        task = self.task_service.find_task(task_id)
        if task.completed == checked:
            return
        try:
            self.task_service.toggle_task(
                task_id,
                allow_early_completion=self.allow_early_completion,
            )
        except ValueError as error:
            row.set_completed(task.completed)
            self.show_status(str(error), True)
            return
        row.set_completed(task.completed)
        self._update_summary()
        self.tasks_changed.emit()

    def _show_task_menu(self, button, task):
        menu = QMenu(self)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        chosen = menu.exec(button.mapToGlobal(QPoint(0, button.height())))
        if chosen == edit_action:
            self.open_edit_dialog(task)
        elif chosen == delete_action:
            self.delete_task(task)

    def _exec_modal(self, dialog):
        self.modal_state_changed.emit(True)
        try:
            return dialog.exec()
        finally:
            self.modal_state_changed.emit(False)

    def open_calendar(self):
        dialog = CalendarDialog(
            self.selected_date,
            self.task_service.tasks,
            self.theme,
            self,
        )
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.select_date(dialog.selected_date)

    def open_add_dialog(self):
        if self.selected_date < date.today():
            return
        dialog = TaskDialog(
            self.task_service,
            self.selected_date,
            theme_name=self.theme,
            parent=self,
        )
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.selected_date = date.fromisoformat(dialog.saved_task.task_date)
            self.tasks_changed.emit()
            self.refresh_tasks()

    def open_edit_dialog(self, task):
        dialog = TaskDialog(
            self.task_service,
            task=task,
            theme_name=self.theme,
            parent=self,
        )
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.selected_date = date.fromisoformat(dialog.saved_task.task_date)
            self.tasks_changed.emit()
            self.refresh_tasks()

    def delete_task(self, task):
        if task.repeat_rule != "none":
            dialog = RecurringDeleteDialog(task, self.theme, self)
            if self._exec_modal(dialog) != QDialog.DialogCode.Accepted:
                return
            try:
                self.task_service.delete_recurring(task.task_id, dialog.scope)
            except ValueError as error:
                self.show_status(str(error), True)
                return
            self.tasks_changed.emit()
            self.refresh_tasks()
            return

        self.modal_state_changed.emit(True)
        try:
            answer = QMessageBox.question(
                self,
                "删除任务",
                f"确定删除“{task.title}”吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
        finally:
            self.modal_state_changed.emit(False)
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.task_service.delete_task(task.task_id)
            except ValueError as error:
                self.show_status(str(error), True)
                return
            self.tasks_changed.emit()
            self.refresh_tasks()

    def apply_appearance(self, theme=None, font_size=None):
        if theme in THEMES:
            self.theme = theme
        if isinstance(font_size, int) and not isinstance(font_size, bool):
            self.font_size = max(12, min(font_size, 22))
        scale = max(0.86, min(self.width() / 490, 1.38))
        self._last_scale = scale
        self.setStyleSheet(note_style(self.theme, self.font_size, scale))
        self.paper.set_theme(self.theme)
        self.add_button.set_theme(self.theme)
        self.settings_button.set_theme(self.theme)
        for button in self.findChildren(CircleButton):
            button.set_theme(self.theme)
            diameter = max(30, round(36 * scale))
            button.set_diameter(diameter)
        colors = THEMES[self.theme]
        self.paper_shadow.setColor(QColor(*colors["shadow"]))
        add_size = max(40, round(48 * scale))
        self.add_button.setFixedSize(add_size, add_size)
        accent = colors["accent"]
        for row in self.task_container.findChildren(TaskRow):
            row.set_accent(accent)
        self._update_quote()

    def _sync_quote_to_selected_date(self):
        """让文案日期始终跟随当前正在查看的任务日期。"""
        if self._quote_date != self.selected_date:
            self._quote_date = self.selected_date
            self.quote_text = get_daily_quote(self.selected_date)
            self._update_quote()
            return

        # 日期没变时也重新适配一次，兼顾窗口缩放和主题切换。
        QTimer.singleShot(0, self._fit_quote_height)

    def _update_quote(self):
        self.quote_label.setText(self.quote_text)
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        QTimer.singleShot(0, self._fit_quote_height)

    def _fit_quote_height(self):
        """让短文案尽量放大；最小字号仍放不下时才显示滚动条。"""
        if not hasattr(self, "quote_label"):
            return

        scale = self._last_scale or 1.0
        box_height = max(72, round(84 * scale))
        self.quote_scroll.setFixedHeight(box_height)

        available_width = max(120, self.quote_scroll.viewport().width() - 12)
        available_height = max(46, box_height - 8)
        minimum_size = max(11, round(12 * scale))
        # 短文案可以继续放大；长文案则逐级缩小，直到完整装进框内。
        maximum_size = max(minimum_size, round(42 * scale))
        flags = Qt.TextFlag.TextWordWrap.value | Qt.AlignmentFlag.AlignHCenter.value
        measure_box = QRect(0, 0, available_width, 10_000)

        chosen_size = minimum_size
        natural_height = 0
        font = self.quote_label.font()
        for pixel_size in range(maximum_size, minimum_size - 1, -1):
            font.setPixelSize(pixel_size)
            measured = QFontMetrics(font).boundingRect(measure_box, flags, self.quote_text)
            chosen_size = pixel_size
            natural_height = measured.height() + 6
            if natural_height <= available_height:
                break

        font.setPixelSize(chosen_size)
        self.quote_label.setFont(font)
        needs_scroll = natural_height > available_height
        minimum_content_height = natural_height + 4 if needs_scroll else 0
        self.quote_label.setMinimumHeight(minimum_content_height)
        self.quote_content.setMinimumHeight(minimum_content_height)
        self.quote_content_layout.invalidate()
        policy = (
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
            if needs_scroll
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.quote_scroll.setVerticalScrollBarPolicy(policy)
        if not needs_scroll:
            self.quote_scroll.verticalScrollBar().setValue(0)

    def restore_default_size(self):
        self.resize(490, 710)
        self.show_status("已恢复默认大小")

    def set_allow_early_completion(self, enabled):
        self.allow_early_completion = bool(enabled)
        self.refresh_tasks()

    def show_status(self, text, is_error=False):
        color = THEMES[self.theme]["danger"] if is_error else THEMES[self.theme]["muted"]
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)
        self.status_timer.start(5000 if is_error else 2500)

    def current_settings(self):
        return {
            "theme": self.theme,
            "font_size": self.font_size,
            "allow_early_completion": self.allow_early_completion,
            "window_width": self.width(),
            "window_height": self.height(),
            "window_x": self.x(),
            "window_y": self.y(),
        }

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._initialized:
            self.geometry_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "paper"):
            return
        scale = max(0.86, min(self.width() / 490, 1.38))
        if self._last_scale is None or abs(scale - self._last_scale) >= 0.06:
            self.apply_appearance()
        else:
            QTimer.singleShot(0, self._fit_quote_height)
        if self._initialized:
            self.geometry_changed.emit()

    def closeEvent(self, event):
        event.ignore()
        self.close_requested.emit()
