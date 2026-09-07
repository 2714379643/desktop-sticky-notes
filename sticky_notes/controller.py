"""连接数据、界面、设置和自动保存。"""

from datetime import datetime

from PySide6.QtCore import QPoint, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QDialog, QMessageBox

from sticky_notes.desktop_windows import apply_bottom_layer
from sticky_notes.storage import DEFAULT_SETTINGS, StorageError, TaskStorage
from sticky_notes.task_service import TaskService
from sticky_notes.ui.note_window import NoteWindow
from sticky_notes.ui.settings_dialog import SettingsDialog


class AppController:
    """应用控制器：数据改变后合并保存，并每 30 秒兜底检查。"""

    def __init__(self, storage=None):
        self.storage = storage or TaskStorage()
        self.saving_enabled = True
        self.startup_error = None
        self.recovered_from_backup = False

        try:
            tasks, settings, self.recovered_from_backup = self.storage.load()
        except StorageError as error:
            # 不用空列表覆盖损坏文件；允许用户打开界面查看错误。
            tasks, settings = [], DEFAULT_SETTINGS.copy()
            self.saving_enabled = False
            self.startup_error = str(error)

        self.settings = settings
        self.task_service = TaskService(tasks)
        self.window = NoteWindow(self.task_service, settings)
        self.bottom_enabled = settings.get("stay_on_bottom", True)
        self.dirty = False
        self.ready = False

        self.save_timer = QTimer(self.window)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(self.save_now)

        self.autosave_timer = QTimer(self.window)
        self.autosave_timer.setInterval(30_000)
        self.autosave_timer.timeout.connect(self.save_if_needed)

        self.window.tasks_changed.connect(self.mark_dirty)
        self.window.settings_requested.connect(self.open_settings)
        self.window.modal_state_changed.connect(self._handle_modal_state)
        self.window.geometry_changed.connect(self._geometry_changed)
        self._restore_window_position()

    def start(self):
        self.window.show()
        self.ready = True
        self.autosave_timer.start()
        QTimer.singleShot(0, lambda: apply_bottom_layer(self.window, self.bottom_enabled))
        QTimer.singleShot(80, self._show_startup_message)

        # 首次启动创建数据文件；旧版无 task_id 的数据也会在这里升级。
        if self.saving_enabled:
            self.mark_dirty()

    def mark_dirty(self):
        if not self.saving_enabled:
            return
        self.dirty = True
        self.window.show_status("等待自动保存…")
        self.save_timer.start()

    def save_if_needed(self):
        if self.dirty:
            self.save_now()

    def save_now(self):
        if not self.saving_enabled or not self.dirty:
            return

        self.settings.update(self.window.current_settings())
        self.settings["stay_on_bottom"] = self.bottom_enabled
        try:
            self.storage.save(self.task_service.tasks, self.settings)
        except (StorageError, TypeError, ValueError) as error:
            self.dirty = True
            self.window.show_status("保存失败，请检查磁盘空间或权限", True)
            return

        self.dirty = False
        self.window.show_status(f"已自动保存 · {datetime.now():%H:%M:%S}")

    def open_settings(self):
        current = dict(self.settings)
        current.update(self.window.current_settings())
        current["stay_on_bottom"] = self.bottom_enabled
        dialog = SettingsDialog(current, self.window)

        self._handle_modal_state(True)
        try:
            result = dialog.exec()
        finally:
            self._handle_modal_state(False)

        if result != QDialog.DialogCode.Accepted:
            return

        self.settings = dialog.accepted_settings
        self.bottom_enabled = self.settings["stay_on_bottom"]
        self.window.apply_appearance(
            self.settings["theme"],
            self.settings["font_size"],
        )
        apply_bottom_layer(self.window, self.bottom_enabled)
        self.mark_dirty()

    def _handle_modal_state(self, opened):
        # 置底主窗口打开对话框时临时恢复普通层级，避免对话框藏在应用后面。
        apply_bottom_layer(self.window, False if opened else self.bottom_enabled)

    def _geometry_changed(self):
        if self.ready:
            self.mark_dirty()

    def _restore_window_position(self):
        x = self.settings.get("window_x")
        y = self.settings.get("window_y")
        if x is None or y is None:
            return

        screen = QGuiApplication.screenAt(QPoint(x, y))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        area = screen.availableGeometry()
        max_x = max(area.left(), area.right() - self.window.width() + 1)
        max_y = max(area.top(), area.bottom() - self.window.height() + 1)
        safe_x = min(max(x, area.left()), max_x)
        safe_y = min(max(y, area.top()), max_y)
        self.window.move(safe_x, safe_y)

    def _show_startup_message(self):
        if self.startup_error:
            self.window.show_status("数据文件损坏，已停止保存", True)
            self._handle_modal_state(True)
            try:
                QMessageBox.critical(
                    self.window,
                    "无法读取任务数据",
                    f"{self.startup_error}\n\n为防止覆盖原文件，本次运行不会保存新数据。",
                )
            finally:
                self._handle_modal_state(False)
        elif self.recovered_from_backup:
            self._handle_modal_state(True)
            try:
                QMessageBox.warning(
                    self.window,
                    "已恢复备份",
                    "主数据文件无法读取，程序已从上一份有效备份恢复。",
                )
            finally:
                self._handle_modal_state(False)

    def shutdown(self):
        self.save_timer.stop()
        self.autosave_timer.stop()
        self.save_now()
