"""便签外观与窗口层级设置。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from sticky_notes.themes import THEMES, dialog_style


class SettingsDialog(QDialog):
    """确认后从 accepted_settings 读取新设置；取消不会修改原字典。"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.original_settings = dict(settings)
        self.accepted_settings = None

        self.setWindowTitle("便签设置")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(380)
        self.setStyleSheet(dialog_style())
        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(15)

        heading = QLabel("便签设置")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        form = QFrame()
        form.setObjectName("form")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        form_layout.addWidget(self._label("纸张颜色"))
        self.theme_input = QComboBox()
        self.theme_input.addItems(THEMES.keys())
        self.theme_input.setCurrentText(self.original_settings.get("theme", "奶油纸"))
        form_layout.addWidget(self.theme_input)

        form_layout.addWidget(self._label("任务字号"))
        self.font_input = QSpinBox()
        self.font_input.setRange(12, 22)
        self.font_input.setSuffix(" px")
        self.font_input.setValue(self.original_settings.get("font_size", 15))
        form_layout.addWidget(self.font_input)

        self.bottom_input = QCheckBox("默认位于普通应用下方")
        self.bottom_input.setChecked(
            self.original_settings.get("stay_on_bottom", True)
        )
        self.bottom_input.setToolTip("便签仍位于桌面壁纸上方")
        form_layout.addWidget(self.bottom_input)
        layout.addWidget(form)

        self.preview = QFrame()
        self.preview.setMinimumHeight(92)
        preview_layout = QVBoxLayout(self.preview)
        preview_layout.setContentsMargins(16, 12, 16, 12)
        preview_layout.addWidget(QLabel("9.7 To do list"))
        self.preview_text = QLabel("□ 整理今天的学习内容")
        preview_layout.addWidget(self.preview_text)
        layout.addWidget(self.preview)

        note = QLabel("任务与设置会自动保存；切换主题不会清空任务。")
        note.setObjectName("secondary")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_button = QPushButton("取消")
        apply_button = QPushButton("应用")
        apply_button.setObjectName("primaryButton")
        apply_button.setDefault(True)
        buttons.addWidget(cancel_button)
        buttons.addWidget(apply_button)
        layout.addLayout(buttons)

        cancel_button.clicked.connect(self.reject)
        apply_button.clicked.connect(self.submit)
        self.theme_input.currentTextChanged.connect(self._update_preview)
        self.font_input.valueChanged.connect(self._update_preview)

    @staticmethod
    def _label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _update_preview(self, *unused):
        colors = THEMES[self.theme_input.currentText()]
        self.preview.setStyleSheet(
            f"QFrame {{ background: {colors['paper']}; "
            f"border: 1px solid {colors['border']}; border-radius: 9px; }} "
            "QLabel { border: none; background: transparent; }"
        )
        font = self.preview_text.font()
        font.setPixelSize(self.font_input.value())
        self.preview_text.setFont(font)

    def submit(self):
        updated = dict(self.original_settings)
        updated.update(
            {
                "theme": self.theme_input.currentText(),
                "font_size": self.font_input.value(),
                "stay_on_bottom": self.bottom_input.isChecked(),
            }
        )
        self.accepted_settings = updated
        self.accept()
