"""跨主题的圆形控件；不依赖 Windows 原生方形按钮外观。"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QComboBox, QListView, QPushButton

from sticky_notes.themes import THEMES


class CircleButton(QPushButton):
    """固定正方形占位，绘制正圆，保留键盘、点击和禁用语义。"""

    def __init__(self, text="", theme_name="雾光玻璃", parent=None, diameter=36):
        super().__init__(text, parent)
        self.theme_name = theme_name
        self.setObjectName("circleControl")
        self.set_diameter(diameter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoDefault(False)

    def set_diameter(self, diameter):
        """Qt 的 QSS 最小尺寸优先于 setFixedSize，必须同步锁定样式尺寸。"""
        self.setFixedSize(diameter, diameter)
        self.setStyleSheet(
            "QPushButton#circleControl { "
            f"min-width: {diameter}px; max-width: {diameter}px; "
            f"min-height: {diameter}px; max-height: {diameter}px; "
            "padding: 0px; border: none; background: transparent; }"
        )

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def hitButton(self, pos):
        delta = QPointF(pos) - QRectF(self.rect()).center()
        return delta.x() ** 2 + delta.y() ** 2 <= (min(self.width(), self.height()) / 2) ** 2

    def paintEvent(self, event):
        colors = THEMES.get(self.theme_name, THEMES["雾光玻璃"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0 if self.isEnabled() else 0.42)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        if self.isDown():
            rect.adjust(1, 1, -1, -1)
        fill = QColor(*colors["surface"])
        fill.setAlpha(115 if self.underMouse() else 72)
        painter.setBrush(fill)
        painter.setPen(QPen(QColor(*colors["edge"]), 1.2))
        painter.drawEllipse(rect)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(colors["accent"]), 1.4))
            painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        painter.setPen(QColor(colors["text"]))
        font = self.font()
        font.setPixelSize(round(self.width() * 0.53))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class RoundCheckBox(QCheckBox):
    """圆形复选标记，仍支持多个设置同时启用，不是互斥单选。"""

    def __init__(self, text, theme_name="雾光玻璃", parent=None):
        super().__init__(text, parent)
        self.theme_name = theme_name
        self.setMinimumHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 36, 28)

    def minimumSizeHint(self):
        return self.sizeHint()

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        colors = THEMES.get(self.theme_name, THEMES["雾光玻璃"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0 if self.isEnabled() else 0.42)
        cy = self.height() / 2
        painter.setPen(QPen(QColor(colors["accent"] if self.isChecked() else colors["muted"]), 1.3))
        painter.setBrush(QColor(colors["accent"]) if self.isChecked() else Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(12, cy), 9.5, 9.5)
        if self.isChecked():
            pen = QPen(QColor(colors.get("accent_text", "white")), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(7.5, cy), QPointF(10.5, cy + 3))
            painter.drawLine(QPointF(10.5, cy + 3), QPointF(16.5, cy - 3.5))
        painter.setPen(QColor(colors["text"]))
        painter.drawText(QRectF(32, 0, self.width() - 32, self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(colors["accent"]), 1, Qt.PenStyle.DotLine))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)


class ThemeComboBox(QComboBox):
    """显式绘制圆形箭头区，不依赖 QSS 已被隐藏的原生箭头。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_name = "雾光玻璃"
        self.setObjectName("themeCombo")
        self.setView(QListView(self))
        self.setMaxVisibleItems(len(THEMES))
        self.setAccessibleName("主题风格，点击展开选择")

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        colors = THEMES.get(self.theme_name, THEMES["雾光玻璃"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() - 19, self.height() / 2
        fill = QColor(*colors["surface"])
        fill.setAlpha(150)
        painter.setBrush(fill)
        painter.setPen(QPen(QColor(*colors["edge"]), 1))
        painter.drawEllipse(QPointF(cx, cy), 12, 12)
        pen = QPen(QColor(colors["text"]), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(cx - 4, cy - 2), QPointF(cx, cy + 2))
        painter.drawLine(QPointF(cx, cy + 2), QPointF(cx + 4, cy - 2))
