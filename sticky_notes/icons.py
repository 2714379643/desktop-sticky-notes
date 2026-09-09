"""不依赖外部图片的应用与托盘图标。"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def create_app_icon(size=64):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    shadow = QColor(37, 48, 55, 45)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(shadow)
    painter.drawRoundedRect(QRectF(12, 13, 43, 43), 11, 11)
    painter.setBrush(QColor("#eef3f4"))
    painter.setPen(QPen(QColor("#ffffff"), 1.5))
    painter.drawRoundedRect(QRectF(8, 8, 44, 44), 11, 11)

    pen = QPen(QColor("#7788bd"), 3.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    for y, width in ((22, 23), (31, 18), (40, 25)):
        painter.drawLine(QPointF(18, y), QPointF(18 + width, y))
    painter.end()
    return QIcon(pixmap)
