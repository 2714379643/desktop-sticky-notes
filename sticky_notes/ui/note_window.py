"""桌面便签主窗口。"""

from datetime import date

from PySide6.QtCore import QDate, QLocale, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
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
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from sticky_notes.task_service import TaskService
from sticky_notes.themes import THEMES, dialog_style, note_style
from sticky_notes.ui.task_dialog import TaskDialog


def to_qdate(value):
    return QDate(value.year, value.month, value.day)


class PinHandle(QWidget):
    """自绘图钉，并作为无边框窗口的拖动区域。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(33)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("按住并拖动便签")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x = self.width() // 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(82, 42, 31, 42))
        painter.drawEllipse(center_x - 7, 10, 23, 19)
        gradient = QRadialGradient(center_x - 4, 7, 19)
        gradient.setColorAt(0, QColor("#f3b9a8"))
        gradient.setColorAt(0.5, QColor("#b65c48"))
        gradient.setColorAt(1, QColor("#7d3429"))
        painter.setBrush(gradient)
        painter.drawEllipse(center_x - 11, 2, 22, 22)

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


class TaskCheckBox(QCheckBox):
    """在浅色便签上保持清晰的方框和勾选标记。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(25, 25)

    def hitButton(self, position):
        return self.rect().contains(position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0 if self.isEnabled() else 0.52)
        border = "#77825d" if self.isChecked() else "#a69c7d"
        fill = "#77825d" if self.isChecked() else "#fffaf0"
        painter.setPen(QPen(QColor(border), 1.3))
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(2, 2, 20, 20, 5, 5)
        if self.isChecked():
            painter.setPen(
                QPen(
                    QColor("#fffdf2"),
                    2.2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            painter.drawLine(7, 12, 11, 16)
            painter.drawLine(11, 16, 18, 8)


class CalendarDialog(QDialog):
    """选择查看日期；过去日期也允许选择。"""

    def __init__(self, selected_date, tasks, parent=None):
        super().__init__(parent)
        self.selected_date = selected_date
        self.setWindowTitle("选择查看日期")
        self.setMinimumSize(370, 360)
        self.setStyleSheet(dialog_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        month_row = QHBoxLayout()
        previous_button = QPushButton("‹")
        next_button = QPushButton("›")
        previous_button.setFixedWidth(42)
        next_button.setFixedWidth(42)
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setObjectName("heading")
        month_row.addWidget(previous_button)
        month_row.addWidget(self.month_label, 1)
        month_row.addWidget(next_button)
        layout.addLayout(month_row)

        self.calendar = QCalendarWidget()
        self.calendar.setLocale(QLocale(QLocale.Language.Chinese, QLocale.Country.China))
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setGridVisible(False)
        self.calendar.setSelectedDate(to_qdate(selected_date))
        self._mark_task_dates(tasks)
        layout.addWidget(self.calendar, 1)

        footer = QHBoxLayout()
        hint = QLabel("带下划线的日期有任务")
        hint.setObjectName("secondary")
        today_button = QPushButton("回到今天")
        footer.addWidget(hint, 1)
        footer.addWidget(today_button)
        layout.addLayout(footer)

        previous_button.clicked.connect(self.calendar.showPreviousMonth)
        next_button.clicked.connect(self.calendar.showNextMonth)
        self.calendar.currentPageChanged.connect(self._update_month)
        self.calendar.clicked.connect(self._pick)
        self.calendar.activated.connect(self._pick)
        today_button.clicked.connect(lambda: self._pick(QDate.currentDate()))
        self._update_month(self.calendar.yearShown(), self.calendar.monthShown())

    def _mark_task_dates(self, tasks):
        for task_date in {task.task_date for task in tasks}:
            chosen = QDate.fromString(task_date, "yyyy-MM-dd")
            if chosen.isValid():
                text_format = QTextCharFormat()
                text_format.setFontUnderline(True)
                text_format.setUnderlineColor(QColor("#78835d"))
                self.calendar.setDateTextFormat(chosen, text_format)

    def _update_month(self, year, month):
        self.month_label.setText(f"{year}年{month}月")

    def _pick(self, chosen):
        self.selected_date = chosen.toPython()
        self.accept()


class NoteWindow(QWidget):
    """便签主窗口；数据变化交给 Controller 保存。"""

    tasks_changed = Signal()
    settings_requested = Signal()
    modal_state_changed = Signal(bool)
    geometry_changed = Signal()

    def __init__(self, task_service, settings=None, parent=None):
        super().__init__(parent)
        if not isinstance(task_service, TaskService):
            raise TypeError("task_service 必须是 TaskService 对象")

        self.task_service = task_service
        self.settings = dict(settings or {})
        self.selected_date = date.today()
        self.theme = self.settings.get("theme", "奶油纸")
        if self.theme not in THEMES:
            self.theme = "奶油纸"
        self.font_size = self.settings.get("font_size", 15)
        if isinstance(self.font_size, bool) or not isinstance(self.font_size, int):
            self.font_size = 15
        self.font_size = max(12, min(self.font_size, 22))

        self.setWindowTitle("桌面便签")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(420, 580)
        self.resize(
            self._positive_setting("window_width", 490),
            self._positive_setting("window_height", 710),
        )
        self._build_ui()
        self.apply_appearance()
        self.refresh_tasks()

    def _positive_setting(self, key, default):
        value = self.settings.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return default
        return value

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 24)
        self.paper = QFrame()
        self.paper.setObjectName("paper")
        self.paper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        shadow = QGraphicsDropShadowEffect(self.paper)
        shadow.setBlurRadius(25)
        shadow.setOffset(1, 6)
        shadow.setColor(QColor(57, 45, 24, 55))
        self.paper.setGraphicsEffect(shadow)
        outer.addWidget(self.paper)

        layout = QVBoxLayout(self.paper)
        layout.setContentsMargins(25, 4, 25, 21)
        layout.setSpacing(12)
        layout.addWidget(PinHandle())

        toolbar = QHBoxLayout()
        self.calendar_button = QPushButton()
        self.calendar_button.setObjectName("dateButton")
        self.calendar_button.setToolTip("切换查看日期")
        self.calendar_button.clicked.connect(self.open_calendar)
        toolbar.addWidget(self.calendar_button)
        toolbar.addStretch()
        settings_button = QPushButton("⚙")
        settings_button.setObjectName("iconButton")
        settings_button.setAccessibleName("设置")
        settings_button.clicked.connect(self.settings_requested.emit)
        toolbar.addWidget(settings_button)
        close_button = QPushButton("×")
        close_button.setObjectName("iconButton")
        close_button.setAccessibleName("关闭")
        close_button.clicked.connect(self.close)
        toolbar.addWidget(close_button)
        layout.addLayout(toolbar)

        eyebrow = QLabel("留一点空间，做好今天。")
        eyebrow.setObjectName("secondary")
        layout.addWidget(eyebrow)
        self.heading_label = QLabel()
        self.heading_label.setObjectName("heading")
        self.heading_label.setWordWrap(True)
        layout.addWidget(self.heading_label)
        self.day_label = QLabel()
        self.day_label.setObjectName("secondary")
        layout.addWidget(self.day_label)

        summary = QHBoxLayout()
        self.count_label = QLabel()
        self.percent_label = QLabel()
        summary.addWidget(self.count_label)
        summary.addStretch()
        summary.addWidget(self.percent_label)
        layout.addLayout(summary)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        layout.addWidget(self.progress_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 6, 0, 6)
        self.task_layout.setSpacing(0)
        scroll.setWidget(self.task_container)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        today_button = QPushButton("↶ 回到今天")
        today_button.clicked.connect(lambda: self.select_date(date.today()))
        footer.addWidget(today_button)
        footer.addStretch()
        self.add_button = QPushButton("＋ 添加任务")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.open_add_dialog)
        footer.addWidget(self.add_button)
        layout.addLayout(footer)
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("secondary")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def select_date(self, selected_date):
        if not isinstance(selected_date, date):
            raise TypeError("selected_date 必须是 date 对象")
        self.selected_date = selected_date
        self.refresh_tasks()

    def refresh_tasks(self):
        selected = self.selected_date
        is_past = selected < date.today()
        tasks = self.task_service.get_tasks_by_date(selected.isoformat())
        self.calendar_button.setText(f"{selected.year}年{selected.month}月  ▾")
        self.heading_label.setText(
            f"{selected.year}.{selected.month}.{selected.day} To do list"
        )
        scene = "历史记录" if is_past else "今天" if selected == date.today() else "提前安排"
        weekday = "一二三四五六日"[selected.weekday()]
        self.day_label.setText(f"{scene} · 星期{weekday}")

        completed, total, percentage = self.task_service.completion_for_date(
            selected.isoformat()
        )
        self.count_label.setText(f"已完成 {completed} / {total} 项")
        self.percent_label.setText(f"{percentage}%" if total else "暂无任务")
        self.progress_bar.setValue(percentage)
        self.add_button.setEnabled(not is_past)
        self.add_button.setText("历史仅查看" if is_past else "＋ 添加任务")

        self._clear_rows()
        if not tasks:
            empty = QLabel("这一天没有记录" if is_past else "这一天，还留着空白。")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_layout.addWidget(empty, 1)
        else:
            for task in tasks:
                self.task_layout.addWidget(self._create_task_row(task, is_past))
        self.task_layout.addStretch()

    def _clear_rows(self):
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    def _create_task_row(self, task, is_past):
        row = QFrame()
        row.setObjectName("taskRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 16, 2, 16)
        row_layout.setSpacing(13)
        checkbox = TaskCheckBox()
        checkbox.setAccessibleName(task.title)
        checkbox.setChecked(task.completed)
        checkbox.setEnabled(not is_past)
        checkbox.toggled.connect(
            lambda checked, task_id=task.task_id: self._toggle_task(task_id, checked)
        )
        row_layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignTop)

        texts = QVBoxLayout()
        texts.setSpacing(6)
        title = QLabel(task.title)
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setWordWrap(True)
        font = title.font()
        font.setStrikeOut(task.completed)
        title.setFont(font)
        title.setProperty("completed", task.completed)
        texts.addWidget(title)
        if task.start_time is not None:
            time_label = QLabel(f"{task.start_time} — {task.end_time}")
            time_label.setObjectName("secondary")
            texts.addWidget(time_label)
        row_layout.addLayout(texts, 1)

        if not is_past:
            more = QPushButton("⋯")
            more.setObjectName("iconButton")
            more.setAccessibleName(f"{task.title}的更多操作")
            more.clicked.connect(
                lambda checked=False, button=more, current=task: self._show_task_menu(
                    button, current
                )
            )
            row_layout.addWidget(more, 0, Qt.AlignmentFlag.AlignTop)
        return row

    def _toggle_task(self, task_id, checked):
        task = self.task_service.find_task(task_id)
        if task.completed != checked:
            try:
                self.task_service.toggle_task(task_id)
            except ValueError as error:
                self.show_status(str(error), True)
                self.refresh_tasks()
                return
            self.tasks_changed.emit()
        self.refresh_tasks()

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
        dialog = CalendarDialog(self.selected_date, self.task_service.tasks, self)
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.select_date(dialog.selected_date)

    def open_add_dialog(self):
        if self.selected_date < date.today():
            return
        dialog = TaskDialog(self.task_service, self.selected_date, parent=self)
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.selected_date = date.fromisoformat(dialog.saved_task.task_date)
            self.tasks_changed.emit()
            self.refresh_tasks()

    def open_edit_dialog(self, task):
        dialog = TaskDialog(self.task_service, task=task, parent=self)
        if self._exec_modal(dialog) == QDialog.DialogCode.Accepted:
            self.selected_date = date.fromisoformat(dialog.saved_task.task_date)
            self.tasks_changed.emit()
            self.refresh_tasks()

    def delete_task(self, task):
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
        self.setStyleSheet(note_style(self.theme, self.font_size))

    def show_status(self, text, is_error=False):
        color = "#a13e2d" if is_error else "#786f59"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)

    def current_settings(self):
        return {
            "theme": self.theme,
            "font_size": self.font_size,
            "window_width": self.width(),
            "window_height": self.height(),
            "window_x": self.x(),
            "window_y": self.y(),
        }

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.geometry_changed.emit()
