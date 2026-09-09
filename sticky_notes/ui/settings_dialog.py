"""外观与任务数据工具设置。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sticky_notes.themes import THEMES, dialog_style
from sticky_notes.ui.dialog_material import schedule_dialog_material
from sticky_notes.ui.controls import CircleButton, RoundCheckBox, ThemeComboBox
from sticky_notes.data_exchange import TXT_EXAMPLE


class FontSizePicker(QFrame):
    """使用始终可见的减号和加号修改字号。"""

    valueChanged = Signal(int)

    def __init__(self, value=15, parent=None):
        super().__init__(parent)
        self._value = 15
        self.setObjectName("fontPicker")
        self.setMinimumWidth(140)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        self.minus_button = CircleButton("−", diameter=30)
        self.plus_button = CircleButton("+", diameter=30)
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.minus_button)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(self.plus_button)
        self.minus_button.clicked.connect(lambda: self.setValue(self._value - 1))
        self.plus_button.clicked.connect(lambda: self.setValue(self._value + 1))
        self.setValue(value)

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(12, min(int(value), 22))
        changed = value != self._value
        self._value = value
        self.value_label.setText(f"{value} px")
        self.minus_button.setEnabled(value > 12)
        self.plus_button.setEnabled(value < 22)
        if changed:
            self.valueChanged.emit(value)


class SettingsDialog(QDialog):
    """确认后读取 accepted_settings；数据按钮通过 requested_action 返回。"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.original_settings = dict(settings)
        self.accepted_settings = None
        self.requested_action = None

        self.setWindowTitle("桌面便签 1.1 设置")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        self.setStyleSheet(
            dialog_style(self.original_settings.get("theme", "雾光玻璃"))
        )
        self._build_ui()
        self._update_preview()
        self.adjustSize()
        schedule_dialog_material(
            self,
            self.original_settings.get("theme", "雾光玻璃"),
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        surface = QFrame()
        surface.setObjectName("dialogSurface")
        root.addWidget(surface)
        outer = QVBoxLayout(surface)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)
        title_row = QHBoxLayout()
        heading = QLabel("便签设置")
        heading.setObjectName("heading")
        close = CircleButton("×")
        close.clicked.connect(self.reject)
        title_row.addWidget(heading)
        title_row.addStretch()
        title_row.addWidget(close)
        outer.addLayout(title_row)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        appearance = self._section("外观")
        appearance_layout = appearance.layout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.addWidget(self._label("主题风格"), 0, 0)
        grid.addWidget(self._label("任务字号"), 1, 0)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)
        self.theme_input = ThemeComboBox()
        self.theme_input.addItems(THEMES.keys())
        self.theme_input.setCurrentText(self.original_settings.get("theme", "雾光玻璃"))
        self.font_input = FontSizePicker(
            self.original_settings.get("font_size", 15)
        )
        grid.addWidget(self.theme_input, 0, 1)
        grid.addWidget(self.font_input, 1, 1)
        appearance_layout.addLayout(grid)

        self.preview = QFrame()
        self.preview.setFixedHeight(54)
        preview_layout = QVBoxLayout(self.preview)
        preview_layout.setContentsMargins(10, 6, 10, 6)
        self.preview_text = QLabel("✓ 整理今天的学习内容")
        preview_layout.addWidget(self.preview_text)
        appearance_layout.addWidget(self.preview)

        self.bottom_input = RoundCheckBox("默认位于普通应用下方")
        self.bottom_input.setChecked(self.original_settings.get("stay_on_bottom", True))
        self.tray_input = RoundCheckBox("关闭窗口时缩到右下角托盘")
        self.tray_input.setChecked(self.original_settings.get("close_to_tray", True))
        self.early_completion_input = RoundCheckBox("允许提前完成未来日期的任务")
        self.early_completion_input.setChecked(
            self.original_settings.get("allow_early_completion", True)
        )
        appearance_layout.addWidget(self.bottom_input)
        appearance_layout.addWidget(self.tray_input)
        appearance_layout.addWidget(self.early_completion_input)
        reset_size = QPushButton("恢复默认大小（490 × 710）")
        reset_size.setObjectName("dataButton")
        reset_size.clicked.connect(lambda: self._finish_with_action("reset_size"))
        appearance_layout.addWidget(reset_size)
        layout.addWidget(appearance)

        data_section = self._section("任务导入与备份")
        data_layout = data_section.layout()
        data_tip = QLabel("TXT 使用 UTF-8 编码，兼容旧版 TXT / JSON。")
        data_tip.setObjectName("secondary")
        data_tip.setWordWrap(True)
        data_layout.addWidget(data_tip)
        actions = QGridLayout()
        manual_button = QPushButton("手动录入")
        import_button = QPushButton("导入任务")
        export_button = QPushButton("导出备份")
        template_button = QPushButton("查看导入模板")
        template_button.clicked.connect(self._show_template)
        import_button.setToolTip("导入 TXT 或旧版 JSON")
        export_button.setToolTip("导出 JSON、TXT 或 CSV")
        for button in (manual_button, import_button, export_button, template_button):
            button.setObjectName("dataButton")
        actions.addWidget(manual_button, 0, 0)
        actions.addWidget(import_button, 0, 1)
        actions.addWidget(export_button, 1, 0)
        actions.addWidget(template_button, 1, 1)
        data_layout.addLayout(actions)
        manual_button.clicked.connect(lambda: self._finish_with_action("manual_add"))
        import_button.clicked.connect(lambda: self._finish_with_action("import_data"))
        export_button.clicked.connect(lambda: self._finish_with_action("export"))
        layout.addWidget(data_section)
        outer.addWidget(body)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("取消")
        apply_button = QPushButton("应用")
        apply_button.setObjectName("primaryButton")
        apply_button.setDefault(True)
        buttons.addWidget(cancel)
        buttons.addWidget(apply_button)
        outer.addLayout(buttons)
        cancel.clicked.connect(self.reject)
        apply_button.clicked.connect(self.submit)
        self.theme_input.currentTextChanged.connect(self._update_preview)
        self.font_input.valueChanged.connect(self._update_preview)

    @staticmethod
    def _section(title):
        section = QFrame()
        section.setObjectName("section")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)
        heading = QLabel(title)
        heading.setObjectName("fieldLabel")
        layout.addWidget(heading)
        return section

    @staticmethod
    def _label(text):
        label = QLabel(text)
        label.setObjectName("secondary")
        return label

    def _update_preview(self, *unused):
        colors = THEMES[self.theme_input.currentText()]
        # 选择主题时整个设置窗口同步换色，避免深色主题下下拉项文字被背景吞掉。
        self.setStyleSheet(
            dialog_style(self.theme_input.currentText())
            + "QPushButton { min-height: 22px; padding: 5px 10px; }"
        )
        schedule_dialog_material(self, self.theme_input.currentText())
        self.theme_input.set_theme(self.theme_input.currentText())
        for control in self.findChildren(CircleButton) + self.findChildren(RoundCheckBox):
            control.set_theme(self.theme_input.currentText())
        popup_palette = self.theme_input.view().palette()
        popup_background = QColor(*colors["surface"])
        popup_background.setAlpha(255)
        popup_palette.setColor(QPalette.ColorRole.Base, popup_background)
        popup_palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        popup_palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
        popup_palette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(colors.get("accent_text", "white")),
        )
        self.theme_input.view().setPalette(popup_palette)
        self.theme_input.view().setStyleSheet(
            f"QListView {{ background: {popup_background.name()}; color: {colors['text']}; "
            f"border: 1px solid {colors['accent']}; padding: 4px; }} "
            "QListView::item { min-height: 30px; padding: 2px 8px; } "
            f"QListView::item:selected {{ background: {colors['accent']}; "
            f"color: {colors.get('accent_text', 'white')}; }}"
        )
        red, green, blue, alpha = colors["surface"]
        self.preview.setStyleSheet(
            f"QFrame {{ background: rgba({red}, {green}, {blue}, {alpha}); "
            f"border: 1px solid {colors['border']}; border-radius: 12px; }} "
            f"QLabel {{ color: {colors['text']}; border: none; background: transparent; }}"
        )
        font = self.preview_text.font()
        font.setPixelSize(self.font_input.value())
        self.preview_text.setFont(font)

    def _show_template(self):
        """长说明单独打开，设置首页无需横向或纵向滚动。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("TXT 导入模板")
        dialog.setStyleSheet(dialog_style(self.theme_input.currentText()))
        dialog.resize(510, 360)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            "每行一项任务，用英文 | 分隔，保存为 UTF-8。\n"
            "日期格式：YYYY-MM-DD，不能早于今天。\n"
            "时间格式：HH:MM，开始和结束同时填写或同时留空。\n"
            "重复规则：none / daily / weekly / monthly。\n"
            "星期：1-7；每月日期：1-31；每日起止日期可留空。\n\n"
            + TXT_EXAMPLE
        )
        layout.addWidget(text)
        close = QPushButton("关闭")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def _collect_settings(self):
        updated = dict(self.original_settings)
        updated.update(
            {
                "theme": self.theme_input.currentText(),
                "font_size": self.font_input.value(),
                "stay_on_bottom": self.bottom_input.isChecked(),
                "close_to_tray": self.tray_input.isChecked(),
                "allow_early_completion": self.early_completion_input.isChecked(),
            }
        )
        return updated

    def _finish_with_action(self, action):
        self.requested_action = action
        self.submit()

    def submit(self):
        self.accepted_settings = self._collect_settings()
        self.accept()
