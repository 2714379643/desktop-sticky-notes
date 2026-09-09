"""紧凑单月日历：日期只占一行，并允许点选相邻月份日期。"""

from datetime import date

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from sticky_notes.calendar_utils import build_month_rows


class CalendarDayButton(QPushButton):
    """日期按钮；整日完成时在底部绘制红点。"""

    def __init__(self, completed=False, parent=None):
        super().__init__(parent)
        self.completed = completed

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.completed:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e14b52"))
        painter.drawEllipse(QPointF(self.width() / 2, self.height() - 4.6), 2.4, 2.4)


class CompactMonthCalendar(QWidget):
    """替代固定六周的 QCalendarWidget，避免多余的相邻月份行。"""

    date_picked = Signal(object)
    month_changed = Signal(int, int)

    def __init__(
        self,
        selected_date,
        completed_dates=None,
        minimum_date=None,
        maximum_date=None,
        parent=None,
    ):
        super().__init__(parent)
        if not isinstance(selected_date, date):
            raise TypeError("selected_date 必须是 date 对象")

        self.selected_date = selected_date
        self.year = selected_date.year
        self.month = selected_date.month
        self.completed_dates = set(completed_dates or ())
        self.minimum_date = minimum_date
        self.maximum_date = maximum_date
        self.day_buttons = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(5)
        self.grid.setVerticalSpacing(5)
        for column, text in enumerate("一二三四五六日"):
            label = QLabel(text)
            label.setObjectName("calendarWeekday")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(label, 0, column)

        self._render_days()

    def show_previous_month(self):
        year = self.year
        month = self.month - 1
        if month == 0:
            year -= 1
            month = 12
        self.set_month(year, month)

    def show_next_month(self):
        year = self.year
        month = self.month + 1
        if month == 13:
            year += 1
            month = 1
        self.set_month(year, month)

    def set_month(self, year, month):
        build_month_rows(year, month)  # 先校验，避免留下半更新状态。
        self.year = year
        self.month = month
        self._render_days()
        self.month_changed.emit(year, month)

    def set_selected_date(self, selected_date):
        """更新选中日期并立即刷新高亮，不等待弹窗关闭。"""
        if not isinstance(selected_date, date):
            raise TypeError("selected_date 必须是 date 对象")
        self.selected_date = selected_date
        if (selected_date.year, selected_date.month) != (self.year, self.month):
            self.year = selected_date.year
            self.month = selected_date.month
            self.month_changed.emit(self.year, self.month)
        self._render_days()

    def _render_days(self):
        for button in self.day_buttons:
            self.grid.removeWidget(button)
            button.hide()
            button.setParent(None)
            button.deleteLater()
        self.day_buttons.clear()

        rows = build_month_rows(self.year, self.month)
        today = date.today()
        for row_index, week in enumerate(rows, start=1):
            for column, current_date in enumerate(week):
                completed = current_date.isoformat() in self.completed_dates
                button = CalendarDayButton(completed)
                button.setText(str(current_date.day))
                button.setObjectName("calendarDay")
                button.setAccessibleName(current_date.isoformat())
                button.setProperty("outside", current_date.month != self.month)
                button.setProperty("selected", current_date == self.selected_date)
                button.setProperty("today", current_date == today)
                enabled = (
                    (self.minimum_date is None or current_date >= self.minimum_date)
                    and (self.maximum_date is None or current_date <= self.maximum_date)
                )
                button.setEnabled(enabled)
                button.clicked.connect(
                    lambda checked=False, value=current_date: self.date_picked.emit(value)
                )
                self.grid.addWidget(button, row_index, column)
                self.day_buttons.append(button)

        # 每个日期只有一行文字；高度随 5/6 周月份自然变化。
        self.setFixedHeight(31 + len(rows) * 41)
        self.updateGeometry()
