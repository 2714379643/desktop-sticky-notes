"""可复用的紧凑日期按钮与日期弹窗。"""

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from sticky_notes.themes import compact_calendar_style, dialog_style
from sticky_notes.ui.dialog_material import schedule_dialog_material
from sticky_notes.ui.month_calendar import CompactMonthCalendar
from sticky_notes.ui.controls import CircleButton


class DatePickerDialog(QDialog):
    def __init__(self, selected_date, theme_name="雾光玻璃", minimum_date=None, parent=None):
        super().__init__(parent)
        self.selected_date = selected_date
        self.setWindowTitle("选择日期")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(390)
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
        header = QHBoxLayout()
        previous = CircleButton("‹", theme_name)
        following = CircleButton("›", theme_name)
        self.month_label = QLabel()
        self.month_label.setObjectName("calendarMonth")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(previous)
        header.addWidget(self.month_label, 1)
        header.addWidget(following)
        layout.addLayout(header)

        self.calendar = CompactMonthCalendar(
            selected_date,
            minimum_date=minimum_date,
        )
        layout.addWidget(self.calendar)
        previous.clicked.connect(self.calendar.show_previous_month)
        following.clicked.connect(self.calendar.show_next_month)
        self.calendar.month_changed.connect(self._update_month)
        self.calendar.date_picked.connect(self._pick)
        self._update_month(self.calendar.year, self.calendar.month)
        schedule_dialog_material(self, theme_name)
        self.adjustSize()

    def _update_month(self, year, month):
        self.month_label.setText(f"{year}年 {month}月")

    def _pick(self, chosen):
        self.selected_date = chosen
        self.accept()


class DateButton(QPushButton):
    dateChanged = Signal(object)

    def __init__(self, value=None, theme_name="雾光玻璃", minimum_date=None, parent=None):
        super().__init__(parent)
        self._date = value or date.today()
        self.theme_name = theme_name
        self.minimum_date = minimum_date
        self.setObjectName("dateButton")
        self.clicked.connect(self._choose)
        self._refresh_text()

    def date(self):
        return self._date

    def set_date(self, value, enforce_minimum=True):
        if not isinstance(value, date):
            raise TypeError("日期必须是 date 对象")
        if (
            enforce_minimum
            and self.minimum_date is not None
            and value < self.minimum_date
        ):
            raise ValueError("不能选择过去日期")
        if value == self._date:
            return
        self._date = value
        self._refresh_text()
        self.dateChanged.emit(value)

    def _refresh_text(self):
        self.setText(f"{self._date:%Y-%m-%d}  ▾")

    def _choose(self):
        dialog = DatePickerDialog(
            self._date,
            self.theme_name,
            self.minimum_date,
            self.window(),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_date(dialog.selected_date)
