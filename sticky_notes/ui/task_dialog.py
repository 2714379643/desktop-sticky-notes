"""添加和编辑任务窗口。"""

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from sticky_notes.models.task import Task
from sticky_notes.task_service import TaskService
from sticky_notes.themes import dialog_style


class TaskDialog(QDialog):
    """保存成功后，可从 saved_task 取得新增或更新后的 Task。"""

    def __init__(
        self,
        task_service,
        selected_date=None,
        task=None,
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

        today = date.today()
        if task is not None:
            selected_date = date.fromisoformat(task.task_date)
        selected_date = selected_date or today
        selected_date = max(selected_date, today)

        self.setWindowTitle("编辑任务" if task else "添加任务")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(400)
        self.setStyleSheet(dialog_style())

        self._build_ui(selected_date)
        self._fill_task(task)
        self.title_input.setFocus()
        self.title_input.selectAll()

    def _build_ui(self, selected_date):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(15)

        heading = QLabel("编辑这项计划" if self.editing_task else "添加一项计划")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        tip = QLabel("日期必填；时间可以全部留空，也可以填写完整时间段。")
        tip.setObjectName("secondary")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        form = QFrame()
        form.setObjectName("form")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(13)

        form_layout.addWidget(self._field_label("日期"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setMinimumDate(QDate.currentDate())
        self.date_input.setDate(
            QDate(selected_date.year, selected_date.month, selected_date.day)
        )
        form_layout.addWidget(self.date_input)

        time_row = QHBoxLayout()
        time_row.setSpacing(12)
        start_layout = QVBoxLayout()
        end_layout = QVBoxLayout()
        start_layout.setSpacing(6)
        end_layout.setSpacing(6)

        start_layout.addWidget(self._field_label("开始时间（可选）"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("例如 09:00")
        self.start_input.setMaxLength(5)
        start_layout.addWidget(self.start_input)

        end_layout.addWidget(self._field_label("结束时间（可选）"))
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("例如 10:30")
        self.end_input.setMaxLength(5)
        end_layout.addWidget(self.end_input)

        time_row.addLayout(start_layout)
        time_row.addLayout(end_layout)
        form_layout.addLayout(time_row)

        form_layout.addWidget(self._field_label("任务内容"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("例如：复习 Python 的模块与包")
        self.title_input.setMaxLength(100)
        form_layout.addWidget(self.title_input)
        layout.addWidget(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_button = QPushButton("取消")
        save_button = QPushButton("保存修改" if self.editing_task else "添加任务")
        save_button.setObjectName("primaryButton")
        save_button.setDefault(True)
        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)
        layout.addLayout(button_row)

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.submit)
        self.title_input.returnPressed.connect(self.submit)
        for widget in (
            self.title_input,
            self.start_input,
            self.end_input,
            self.date_input,
        ):
            if isinstance(widget, QDateEdit):
                widget.dateChanged.connect(self._clear_error)
            else:
                widget.textChanged.connect(self._clear_error)

    def _fill_task(self, task):
        if task is None:
            return
        self.title_input.setText(task.title)
        self.start_input.setText(task.start_time or "")
        self.end_input.setText(task.end_time or "")

    @staticmethod
    def _field_label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def submit(self):
        task_date = self.date_input.date().toString("yyyy-MM-dd")
        values = (
            self.title_input.text(),
            task_date,
            self.start_input.text(),
            self.end_input.text(),
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

    def _clear_error(self, *unused):
        self.error_label.clear()
        self.error_label.hide()
