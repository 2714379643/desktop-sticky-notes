"""可选 Qt 实测：STICKY_UI_TESTS=1 时验证窗口尺寸与控件交互。"""

import os
import unittest


@unittest.skipUnless(os.environ.get("STICKY_UI_TESTS") == "1", "需要启用 Qt UI 测试")
class UiControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widgets = []

    def tearDown(self):
        for widget in self.widgets:
            widget.close()
            widget.deleteLater()
        self.app.processEvents()

    def test_settings_all_themes_fit_without_scroll(self):
        from PySide6.QtWidgets import QScrollArea, QPushButton
        from sticky_notes.themes import THEMES
        from sticky_notes.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog({})
        self.widgets.append(dialog)
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.width(), 420)
        self.assertEqual(dialog.findChildren(QScrollArea), [])
        for theme in THEMES:
            dialog.theme_input.setCurrentText(theme)
            self.app.processEvents()
            self.assertLessEqual(dialog.height(), 650, theme)
            for button in dialog.findChildren(QPushButton):
                if button.isVisible():
                    position = button.mapTo(dialog, button.rect().topLeft())
                    self.assertGreaterEqual(position.x(), 0)
                    self.assertGreaterEqual(position.y(), 0)
                    self.assertLessEqual(position.x() + button.width(), dialog.width())
                    self.assertLessEqual(position.y() + button.height(), dialog.height())

    def test_circle_buttons_are_square_and_corner_not_clickable(self):
        from PySide6.QtCore import QPoint
        from sticky_notes.ui.controls import CircleButton
        button = CircleButton("×")
        self.widgets.append(button)
        self.assertEqual(button.width(), button.height())
        self.assertFalse(button.hitButton(QPoint(0, 0)))
        self.assertTrue(button.hitButton(button.rect().center()))
        clicked = []
        button.clicked.connect(lambda: clicked.append(True))
        button.click()
        self.assertEqual(clicked, [True])

    def test_round_checks_remain_independent(self):
        from sticky_notes.ui.controls import RoundCheckBox
        first, second = RoundCheckBox("置底"), RoundCheckBox("托盘")
        self.widgets.extend((first, second))
        first.click()
        second.click()
        self.assertTrue(first.isChecked())
        self.assertTrue(second.isChecked())
        first.click()
        self.assertFalse(first.isChecked())
        self.assertTrue(second.isChecked())

    def test_theme_and_font_settings_are_saved(self):
        from sticky_notes.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog({"unrelated": "keep"})
        self.widgets.append(dialog)
        dialog.theme_input.setCurrentText("伊蕾娜旅记")
        dialog.font_input.setValue(22)
        dialog.bottom_input.setChecked(False)
        dialog.submit()
        self.assertEqual(dialog.accepted_settings["theme"], "伊蕾娜旅记")
        self.assertEqual(dialog.accepted_settings["font_size"], 22)
        self.assertFalse(dialog.accepted_settings["stay_on_bottom"])
        self.assertEqual(dialog.accepted_settings["unrelated"], "keep")

    def test_main_buttons_stay_round_after_theme_and_size_changes(self):
        from datetime import date
        from sticky_notes.task_service import TaskService
        from sticky_notes.themes import THEMES
        from sticky_notes.ui.controls import CircleButton
        from sticky_notes.ui.note_window import NoteWindow
        service = TaskService()
        service.add_task("UI 检查", date.today().isoformat())
        window = NoteWindow(service)
        self.widgets.append(window)
        window.show()
        for width in (392, 490, 660):
            window.resize(width, round(width * 710 / 490))
            for theme in THEMES:
                window.apply_appearance(theme)
                self.app.processEvents()
                for button in window.findChildren(CircleButton):
                    self.assertEqual(button.width(), button.height(), theme)
                    self.assertGreaterEqual(button.width(), 30)
                    self.assertEqual(button.theme_name, theme)

    def test_theme_arrow_opens_popup_and_keyboard_selects(self):
        from PySide6.QtCore import Qt, QPoint
        from PySide6.QtTest import QTest
        from sticky_notes.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog({})
        self.widgets.append(dialog)
        dialog.show()
        self.app.processEvents()
        combo = dialog.theme_input
        QTest.mouseClick(combo, Qt.MouseButton.LeftButton,
                         pos=QPoint(combo.width() - 19, combo.height() // 2))
        self.app.processEvents()
        self.assertTrue(combo.view().isVisible())
        QTest.keyClick(combo, Qt.Key.Key_Down)
        QTest.keyClick(combo, Qt.Key.Key_Return)
        self.assertEqual(combo.currentIndex(), 1)


if __name__ == "__main__":
    unittest.main()
