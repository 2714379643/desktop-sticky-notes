"""连接 v1.1 数据、界面、托盘、导入导出和静默自动保存。"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, QTimer
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from sticky_notes.data_exchange import (
    export_csv,
    export_json,
    export_txt,
    import_json,
    import_txt,
)
from sticky_notes.desktop_windows import apply_bottom_layer, apply_glass_backdrop
from sticky_notes.icons import create_app_icon
from sticky_notes.storage import DEFAULT_SETTINGS, StorageError, TaskStorage
from sticky_notes.task_service import TaskService
from sticky_notes.themes import THEMES
from sticky_notes.ui.note_window import NoteWindow
from sticky_notes.ui.settings_dialog import SettingsDialog


class AppController:
    """数据变更后 650 ms 合并保存；定时器只兜底，不重绘界面。"""

    def __init__(self, storage=None):
        self.storage = storage or TaskStorage()
        self.saving_enabled = True
        self.startup_error = None
        self.recovered_from_backup = False
        try:
            tasks, settings, self.recovered_from_backup = self.storage.load()
        except StorageError as error:
            tasks, settings = [], DEFAULT_SETTINGS.copy()
            self.saving_enabled = False
            self.startup_error = str(error)

        self.settings = settings
        self.task_service = TaskService(tasks)
        self.window = NoteWindow(self.task_service, settings)
        self.bottom_enabled = settings.get("stay_on_bottom", True)
        self.close_to_tray = settings.get("close_to_tray", True)
        self.dirty = False
        self.ready = False
        self.quitting = False
        self.tray_icon = None

        self.save_timer = QTimer(self.window)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(650)
        self.save_timer.timeout.connect(self.save_now)
        self.autosave_timer = QTimer(self.window)
        self.autosave_timer.setInterval(30_000)
        self.autosave_timer.timeout.connect(self.save_if_needed)

        self.window.tasks_changed.connect(self.mark_dirty)
        self.window.settings_requested.connect(self.open_settings)
        self.window.modal_state_changed.connect(self._handle_modal_state)
        self.window.geometry_changed.connect(self._geometry_changed)
        self.window.close_requested.connect(self._handle_close_request)
        self._restore_window_position()
        self._setup_tray()

    def start(self):
        self.window.show()
        self.ready = True
        self.autosave_timer.start()
        QTimer.singleShot(0, self._apply_layer_and_glass)
        QTimer.singleShot(100, self._show_startup_message)
        if self.saving_enabled:
            self.mark_dirty()

    def mark_dirty(self):
        """仅标记和启动计时器，不改任何可见控件，避免自动保存闪烁。"""
        if not self.saving_enabled:
            return
        self.dirty = True
        self.save_timer.start()

    def save_if_needed(self):
        if self.dirty:
            self.save_now()

    def save_now(self):
        if not self.saving_enabled or not self.dirty:
            return
        self.settings.update(self.window.current_settings())
        self.settings["stay_on_bottom"] = self.bottom_enabled
        self.settings["close_to_tray"] = self.close_to_tray
        try:
            self.storage.save(self.task_service.tasks, self.settings)
        except (StorageError, TypeError, ValueError) as error:
            self.dirty = True
            self.window.show_status(f"保存失败：{error}", True)
            return
        self.dirty = False

    def open_settings(self):
        current = dict(self.settings)
        current.update(self.window.current_settings())
        current["stay_on_bottom"] = self.bottom_enabled
        current["close_to_tray"] = self.close_to_tray
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
        self.close_to_tray = self.settings["close_to_tray"]
        self.window.set_allow_early_completion(
            self.settings["allow_early_completion"]
        )
        self.window.apply_appearance(
            self.settings["theme"],
            self.settings["font_size"],
        )
        self._apply_layer_and_glass()
        self.mark_dirty()

        actions = {
            "manual_add": self.window.open_add_dialog,
            "import_data": self.import_data,
            "export": self.export_backup,
            "reset_size": self.window.restore_default_size,
        }
        action = actions.get(dialog.requested_action)
        if action is not None:
            QTimer.singleShot(0, action)

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "选择任务导入文件",
            str(self.storage.data_path.parent),
            "支持的任务文件 (*.txt *.json);;TXT 文本 (*.txt);;旧版 JSON (*.json)",
        )
        if not path:
            return
        try:
            result = (
                import_json(path, self.task_service)
                if Path(path).suffix.lower() == ".json"
                else import_txt(path, self.task_service)
            )
        except (OSError, UnicodeError, ValueError) as error:
            self._message(QMessageBox.Icon.Critical, "导入失败", str(error))
            return
        if result.imported:
            self.mark_dirty()
            self.window.refresh_tasks()
        icon = QMessageBox.Icon.Warning if result.errors else QMessageBox.Icon.Information
        self._message(icon, "任务导入结果", result.message)

    def export_backup(self):
        default = self.storage.data_path.parent / f"tasks-{datetime.now():%Y%m%d}.json"
        path, selected_filter = QFileDialog.getSaveFileName(
            self.window,
            "导出任务备份",
            str(default),
            "JSON 完整备份 (*.json);;TXT 模板文本 (*.txt);;CSV 表格 (*.csv)",
        )
        if not path:
            return
        output = Path(path)
        if output.suffix.lower() not in (".json", ".txt", ".csv"):
            extension = ".txt" if "TXT" in selected_filter else ".csv" if "CSV" in selected_filter else ".json"
            output = output.with_suffix(extension)
        try:
            if output.suffix.lower() == ".txt":
                export_txt(output, self.task_service.tasks)
            elif output.suffix.lower() == ".csv":
                export_csv(output, self.task_service.tasks)
            else:
                current = dict(self.settings)
                current.update(self.window.current_settings())
                export_json(output, self.task_service.tasks, current)
        except OSError as error:
            self._message(QMessageBox.Icon.Critical, "导出失败", str(error))
            return
        self.window.show_status(f"已导出：{output.name}")

    def _message(self, icon, title, text):
        self._handle_modal_state(True)
        try:
            box = QMessageBox(icon, title, text, QMessageBox.StandardButton.Ok, self.window)
            box.exec()
        finally:
            self._handle_modal_state(False)

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        app = QApplication.instance()
        self.tray_icon = QSystemTrayIcon(create_app_icon(), app)
        menu = QMenu()
        show_action = QAction("显示便签", menu)
        hide_action = QAction("隐藏便签", menu)
        quit_action = QAction("退出并保存", menu)
        show_action.triggered.connect(self.show_window)
        hide_action.triggered.connect(self.window.hide)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(show_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("桌面便签 1.1")
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_window()

    def _handle_close_request(self):
        if self.close_to_tray and self.tray_icon is not None:
            self.window.hide()
            self.tray_icon.showMessage(
                "桌面便签仍在运行",
                "点击托盘图标可重新打开；右键可退出。",
                QSystemTrayIcon.MessageIcon.Information,
                2200,
            )
        else:
            self.quit_application()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        QTimer.singleShot(0, self._apply_layer_and_glass)

    def quit_application(self):
        if self.quitting:
            return
        self.quitting = True
        self.save_timer.stop()
        self.dirty = True if self.saving_enabled else self.dirty
        self.save_now()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def _apply_layer_and_glass(self):
        apply_bottom_layer(self.window, self.bottom_enabled)
        colors = THEMES[self.window.theme]
        is_glass = colors["mode"] == "glass"
        tint = colors.get("backdrop")
        QTimer.singleShot(
            0,
            lambda enabled=is_glass, value=tint: apply_glass_backdrop(
                self.window,
                enabled,
                value,
            ),
        )

    def _handle_modal_state(self, opened):
        apply_bottom_layer(self.window, False if opened else self.bottom_enabled)
        # Windows 切换窗口层级时可能重建原生窗口句柄，需要重新应用玻璃效果。
        colors = THEMES[self.window.theme]
        is_glass = colors["mode"] == "glass"
        tint = colors.get("backdrop")
        QTimer.singleShot(
            0,
            lambda enabled=is_glass, value=tint: apply_glass_backdrop(
                self.window,
                enabled,
                value,
            ),
        )

    def _geometry_changed(self):
        if self.ready:
            self.mark_dirty()

    def _restore_window_position(self):
        x = self.settings.get("window_x")
        y = self.settings.get("window_y")
        if x is None or y is None:
            return
        screen = QGuiApplication.screenAt(QPoint(x, y)) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        max_x = max(area.left(), area.right() - self.window.width() + 1)
        max_y = max(area.top(), area.bottom() - self.window.height() + 1)
        self.window.move(
            min(max(x, area.left()), max_x),
            min(max(y, area.top()), max_y),
        )

    def _show_startup_message(self):
        if self.startup_error:
            self.window.show_status("数据文件损坏，已停止保存", True)
            self._message(
                QMessageBox.Icon.Critical,
                "无法读取任务数据",
                f"{self.startup_error}\n\n为防止覆盖原文件，本次运行不会保存新数据。",
            )
        elif self.recovered_from_backup:
            self._message(
                QMessageBox.Icon.Warning,
                "已恢复备份",
                "主数据文件无法读取，程序已从上一份有效备份恢复。",
            )

    def shutdown(self):
        self.save_timer.stop()
        self.autosave_timer.stop()
        if self.saving_enabled and not self.quitting:
            self.dirty = True
        self.save_now()
