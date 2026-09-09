"""使用日期按钮与小时/分钟滚轮添加、编辑任务。"""

from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sticky_notes.models.task import Task
from sticky_notes.task_service import TaskService
from sticky_notes.themes import compact_calendar_style, dialog_style
from sticky_notes.ui.date_picker import DateButton
from sticky_notes.ui.dialog_material import schedule_dialog_material
from sticky_notes.ui.month_calendar import CompactMonthCalendar
from sticky_notes.ui.controls import CircleButton

REPEAT_LABELS = {
    "不重复": "none",
    "每天": "daily",
    "每周": "weekly",
    "每月": "monthly",
}
WEEKDAY_LABELS = (
    "星期一",
    "星期二",
    "星期三",
    "星期四",
    "星期五",
    "星期六",
    "星期日",
)


class NumberWheel(QListWidget):
    """可用鼠标滚轮和点击选择数值的轻量滚轮。"""

    def __init__(self, maximum, parent=None):
        super().__init__(parent)
        self.addItems([f"{number:02d}" for number in range(maximum + 1)])
        self.setFixedSize(72, 132)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setCurrentRow(0)

    def value(self):
        return self.currentRow()

    def set_value(self, value):
        value = max(0, min(int(value), self.count() - 1))
        self.setCurrentRow(value)
        self.scrollToItem(
            self.currentItem(),
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self.scrollToItem(
            self.currentItem(),
            QAbstractItemView.ScrollHint.PositionAtCenter,
        ))

    def wheelEvent(self, event):
        step = -1 if event.angleDelta().y() > 0 else 1
        self.set_value(self.currentRow() + step)
        event.accept()


class TimeWheel(QWidget):
    """一组小时和分钟滚轮。"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(title)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        wheels = QHBoxLayout()
        wheels.setSpacing(6)
        self.hour = NumberWheel(23)
        self.minute = NumberWheel(59)
        colon = QLabel(":")
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wheels.addWidget(self.hour)
        wheels.addWidget(colon)
        wheels.addWidget(self.minute)
        layout.addLayout(wheels)

    def set_time(self, value):
        hour, minute = (value or "09:00").split(":")
        self.hour.set_value(hour)
        self.minute.set_value(minute)

    def value(self):
        return f"{self.hour.value():02d}:{self.minute.value():02d}"


class OptionalDatePicker(QWidget):
    """带启用开关的日期按钮，允许开始或结束日期单独留空。"""

    def __init__(self, label, value, theme_name, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.enabled_input = QCheckBox(label)
        self.date_button = DateButton(
            value,
            theme_name,
            minimum_date=date.today(),
        )
        self.date_button.setEnabled(False)
        self.enabled_input.toggled.connect(self.date_button.setEnabled)
        layout.addWidget(self.enabled_input)
        layout.addWidget(self.date_button)

    def value(self):
        return self.date_button.date().isoformat() if self.enabled_input.isChecked() else None

    def set_value(self, value):
        if value is None:
            self.enabled_input.setChecked(False)
            return
        self.date_button.set_date(date.fromisoformat(value), enforce_minimum=False)
        self.enabled_input.setChecked(True)


class TaskDialog(QDialog):
    """保存成功后，可从 saved_task 取得新增或更新后的 Task。"""

    def __init__(
        self,
        task_service,
        selected_date=None,
        task=None,
        theme_name="雾光玻璃",
        parent=None,
    ):
        super().__init__(parent)
        if not isinstance(task_service, TaskService):
            raise TypeError("task_service 必须是 TaskService 对象")
        if task is not None and not isinstance(task, Task):
            raise TypeError("task 必须是 Task 对象或 None")

        self.task_service = task_service
        self.editing_task = task
        self.saved_task = None
        self.theme_name = theme_name

        today = date.today()
        if task is not None:
            selected_date = date.fromisoformat(task.task_date)
        selected_date = max(selected_date or today, today)
        self.selected_date = selected_date

        self.setWindowTitle("编辑任务" if task else "手动添加任务")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(560)
        self.setStyleSheet(
            dialog_style(theme_name) + compact_calendar_style(theme_name)
        )
        self._build_ui(selected_date)
        self._fill_task(task)
        schedule_dialog_material(self, theme_name)
        self.title_input.setFocus()

    def _build_ui(self, selected_date):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        self.dialog_surface = QFrame()
        self.dialog_surface.setObjectName("dialogSurface")
        root.addWidget(self.dialog_surface)
        layout = QVBoxLayout(self.dialog_surface)
        layout.setContentsMargins(24, 21, 24, 22)
        layout.setSpacing(13)

        title_row = QHBoxLayout()
        heading = QLabel("编辑任务" if self.editing_task else "添加任务")
        heading.setObjectName("heading")
        close_button = CircleButton("×", self.theme_name)
        close_button.set_diameter(38)
        close_button.clicked.connect(self.reject)
        title_row.addWidget(heading)
        title_row.addStretch()
        title_row.addWidget(close_button)
        layout.addLayout(title_row)

        form = QFrame()
        form.setObjectName("dialogBody")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)

        calendar_card = QFrame()
        calendar_card.setObjectName("calendarCard")
        calendar_layout = QVBoxLayout(calendar_card)
        calendar_layout.setContentsMargins(17, 15, 17, 16)
        calendar_layout.setSpacing(10)

        calendar_header = QHBoxLayout()
        previous_month = CircleButton("‹", self.theme_name)
        next_month = CircleButton("›", self.theme_name)
        self.calendar_month_label = QLabel()
        self.calendar_month_label.setObjectName("calendarMonth")
        self.calendar_month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calendar_header.addWidget(previous_month)
        calendar_header.addWidget(self.calendar_month_label, 1)
        calendar_header.addWidget(next_month)
        calendar_layout.addLayout(calendar_header)

        completed_dates = self._completed_dates()
        self.calendar = CompactMonthCalendar(
            selected_date,
            completed_dates,
            minimum_date=date.today(),
        )
        calendar_layout.addWidget(self.calendar)
        form_layout.addWidget(calendar_card)
        previous_month.clicked.connect(self.calendar.show_previous_month)
        next_month.clicked.connect(self.calendar.show_next_month)
        self.calendar.month_changed.connect(self._update_calendar_month)
        self.calendar.date_picked.connect(self._pick_calendar_date)
        self._update_calendar_month(self.calendar.year, self.calendar.month)

        form_layout.addWidget(self._field_label("任务名称"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入任务标题...")
        self.title_input.setMaxLength(120)
        form_layout.addWidget(self.title_input)

        repeat_row = QGridLayout()
        repeat_row.setHorizontalSpacing(14)
        repeat_row.addWidget(self._field_label("重复"), 0, 0)
        self.repeat_input = QComboBox()
        self.repeat_input.addItems(REPEAT_LABELS)
        repeat_row.addWidget(self.repeat_input, 0, 1)
        repeat_row.setColumnStretch(1, 1)
        form_layout.addLayout(repeat_row)

        self.repeat_options_panel = QWidget()
        repeat_options = QHBoxLayout(self.repeat_options_panel)
        repeat_options.setContentsMargins(0, 0, 0, 0)
        repeat_options.setSpacing(10)
        self.weekday_label = self._field_label("每周重复于")
        self.weekday_input = QComboBox()
        for weekday, text in enumerate(WEEKDAY_LABELS):
            self.weekday_input.addItem(text, weekday)
        self.monthday_label = self._field_label("每月重复于")
        self.monthday_input = QComboBox()
        for monthday in range(1, 32):
            self.monthday_input.addItem(f"{monthday} 号", monthday)
        repeat_options.addWidget(self.weekday_label)
        repeat_options.addWidget(self.weekday_input, 1)
        repeat_options.addWidget(self.monthday_label)
        repeat_options.addWidget(self.monthday_input, 1)
        form_layout.addWidget(self.repeat_options_panel)

        self.daily_range_panel = QWidget()
        daily_range_layout = QHBoxLayout(self.daily_range_panel)
        daily_range_layout.setContentsMargins(0, 0, 0, 0)
        daily_range_layout.setSpacing(12)
        self.repeat_start_input = OptionalDatePicker(
            "设置开始日期",
            selected_date,
            self.theme_name,
        )
        self.repeat_end_input = OptionalDatePicker(
            "设置结束日期",
            selected_date,
            self.theme_name,
        )
        daily_range_layout.addWidget(self.repeat_start_input, 1)
        daily_range_layout.addWidget(self.repeat_end_input, 1)
        form_layout.addWidget(self.daily_range_panel)

        self.time_enabled = QCheckBox("设置开始与结束时间")
        form_layout.addWidget(self.time_enabled)
        self.time_panel = QWidget()
        time_row = QHBoxLayout(self.time_panel)
        time_row.setContentsMargins(0, 0, 0, 0)
        time_row.setSpacing(22)
        self.start_wheel = TimeWheel("开始时间")
        self.end_wheel = TimeWheel("结束时间")
        self.start_wheel.set_time("09:00")
        self.end_wheel.set_time("10:00")
        time_row.addWidget(self.start_wheel)
        time_row.addWidget(self.end_wheel)
        time_row.addStretch()
        self.time_panel.setVisible(False)
        form_layout.addWidget(self.time_panel)

        layout.addWidget(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        save_button = QPushButton("保存修改" if self.editing_task else "添加任务")
        save_button.setObjectName("primaryButton")
        save_button.setDefault(True)
        save_button.setMinimumHeight(48)
        layout.addWidget(save_button)

        self.repeat_input.currentIndexChanged.connect(self._update_repeat_options)
        self.time_enabled.toggled.connect(self._set_time_panel_visible)
        save_button.clicked.connect(self.submit)
        self.title_input.returnPressed.connect(self.submit)
        self.title_input.textChanged.connect(self._clear_error)
        self._update_repeat_options()

    def _fill_task(self, task):
        if task is None:
            return
        self.title_input.setText(task.title)
        repeat_label = next(
            (label for label, value in REPEAT_LABELS.items() if value == task.repeat_rule),
            "不重复",
        )
        self.repeat_input.setCurrentText(repeat_label)
        if task.generated:
            self.repeat_input.setEnabled(False)
            self.repeat_input.setToolTip("重复规则由系列的第一项任务决定")
            self.weekday_input.setEnabled(False)
            self.monthday_input.setEnabled(False)
        if task.repeat_rule == "weekly":
            self.weekday_input.setCurrentIndex(task.repeat_weekday)
        elif task.repeat_rule == "monthly":
            index = self.monthday_input.findData(task.repeat_monthday)
            self.monthday_input.setCurrentIndex(index)
        self.repeat_start_input.set_value(task.recurrence_start_date)
        self.repeat_end_input.set_value(task.recurrence_end_date)
        if task.generated:
            self.repeat_start_input.setEnabled(False)
            self.repeat_end_input.setEnabled(False)
        if task.start_time is not None:
            self.time_enabled.setChecked(True)
            self.start_wheel.set_time(task.start_time)
            self.end_wheel.set_time(task.end_time)

    @staticmethod
    def _field_label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def submit(self):
        task_date = self.selected_date.isoformat()
        start_time = self.start_wheel.value() if self.time_enabled.isChecked() else None
        end_time = self.end_wheel.value() if self.time_enabled.isChecked() else None
        repeat_rule = REPEAT_LABELS[self.repeat_input.currentText()]
        repeat_weekday = (
            self.weekday_input.currentData()
            if repeat_rule == "weekly"
            else None
        )
        repeat_monthday = (
            self.monthday_input.currentData()
            if repeat_rule == "monthly"
            else None
        )
        values = (
            self.title_input.text(),
            task_date,
            start_time,
            end_time,
            repeat_rule,
            repeat_weekday,
            repeat_monthday,
            self.repeat_start_input.value() if repeat_rule == "daily" else None,
            self.repeat_end_input.value() if repeat_rule == "daily" else None,
        )
        try:
            if self.editing_task is None:
                self.saved_task = self.task_service.add_task(*values)
            else:
                self.saved_task = self.task_service.update_task(
                    self.editing_task.task_id,
                    *values,
                )
        except (TypeError, ValueError) as error:
            self.error_label.setText(str(error))
            self.error_label.show()
            return
        self.accept()

    def _update_repeat_options(self, *unused):
        repeat_rule = REPEAT_LABELS[self.repeat_input.currentText()]
        weekly = repeat_rule == "weekly"
        monthly = repeat_rule == "monthly"
        self.weekday_label.setVisible(weekly)
        self.weekday_input.setVisible(weekly)
        self.monthday_label.setVisible(monthly)
        self.monthday_input.setVisible(monthly)
        self.repeat_options_panel.setVisible(weekly or monthly)
        self.daily_range_panel.setVisible(repeat_rule == "daily")
        self._sync_repeat_defaults()
        self._schedule_content_resize()

    def _sync_repeat_defaults(self, *unused):
        """日期变化时，让新任务的重复选项从所选日期开始。"""
        if self.editing_task is not None:
            return
        selected = self.selected_date
        repeat_rule = REPEAT_LABELS[self.repeat_input.currentText()]
        if repeat_rule == "weekly":
            self.weekday_input.setCurrentIndex(selected.weekday())
        elif repeat_rule == "monthly":
            index = self.monthday_input.findData(selected.day)
            self.monthday_input.setCurrentIndex(index)

    def _set_time_panel_visible(self, visible):
        self.time_panel.setVisible(visible)
        self._schedule_content_resize()

    def _schedule_content_resize(self):
        QTimer.singleShot(0, self._resize_to_contents)

    def _resize_to_contents(self):
        """动态区域关闭后强制恢复内容需要的高度。"""
        current_layout = self.layout()
        if current_layout is None:
            return
        current_layout.invalidate()
        current_layout.activate()
        target_height = self.sizeHint().height()
        self.resize(max(self.width(), self.minimumWidth()), target_height)

    def _clear_error(self, *unused):
        self.error_label.clear()
        self.error_label.hide()

    def _pick_calendar_date(self, chosen):
        self.selected_date = chosen
        self.calendar.set_selected_date(chosen)
        self._clear_error()
        self._sync_repeat_defaults()

    def _update_calendar_month(self, year, month):
        self.calendar_month_label.setText(f"{year} 年 {month} 月")

    def _completed_dates(self):
        tasks_by_date = {}
        for task in self.task_service.tasks:
            if not task.cancelled:
                tasks_by_date.setdefault(task.task_date, []).append(task)
        return {
            task_date
            for task_date, tasks in tasks_by_date.items()
            if tasks and all(task.completed for task in tasks)
        }
