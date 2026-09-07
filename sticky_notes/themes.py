"""集中保存界面颜色与样式。"""


THEMES = {
    "奶油纸": {
        "paper": "#fff5cf",
        "border": "#c6b78f",
        "hover": "#e7ddbb",
        "soft": "rgba(255, 255, 255, 145)",
    },
    "鼠尾草": {
        "paper": "#e7eddc",
        "border": "#aab79d",
        "hover": "#d1dcc5",
        "soft": "rgba(255, 255, 255, 135)",
    },
    "浅玫瑰": {
        "paper": "#f5e1da",
        "border": "#c9aaa0",
        "hover": "#ead0c8",
        "soft": "rgba(255, 255, 255, 140)",
    },
}


def dialog_style(font_size=14):
    return f"""
        QDialog {{ background: #fffaf0; }}
        QWidget {{
            color: #39392f;
            font-family: "Microsoft YaHei", "Noto Sans CJK SC";
            font-size: {font_size}px;
        }}
        QLabel#heading {{ color: #34382c; font-size: 22px; font-weight: 600; }}
        QLabel#secondary {{ color: #7c715d; font-size: 13px; }}
        QLabel#fieldLabel {{ color: #5f5b4c; font-weight: 600; }}
        QLabel#error {{
            color: #a13e2d; background: #f9dfd8;
            border-radius: 7px; padding: 9px 11px;
        }}
        QFrame#form {{
            background: rgba(255, 255, 255, 150);
            border: 1px solid #e0d6bd; border-radius: 10px;
        }}
        QLineEdit, QDateEdit, QComboBox, QSpinBox {{
            min-height: 22px; background: #fffef9;
            border: 1px solid #d5cab0; border-radius: 7px;
            padding: 8px 10px; selection-background-color: #6f7959;
        }}
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border: 1px solid #697450;
        }}
        QPushButton {{
            background: #eee8d7; border: none;
            border-radius: 8px; padding: 9px 15px;
        }}
        QPushButton:hover {{ background: #e2dac5; }}
        QPushButton#primaryButton {{
            background: #48513c; color: #fffbed; font-weight: 600;
        }}
        QPushButton#primaryButton:hover {{ background: #5b654d; }}
        QCalendarWidget QAbstractItemView {{
            background: #fffdf6; selection-background-color: #65724e;
            selection-color: white; outline: none;
        }}
    """


def note_style(theme_name, font_size):
    colors = THEMES.get(theme_name, THEMES["奶油纸"])
    return f"""
        QWidget {{
            color: #39392f;
            font-family: "Microsoft YaHei", "Noto Sans CJK SC";
            font-size: {font_size}px;
        }}
        QFrame#paper {{
            background: {colors['paper']};
            border: 1px solid {colors['border']}; border-radius: 13px;
        }}
        QLabel, QScrollArea, QScrollArea QWidget {{ background: transparent; }}
        QLabel#heading {{ color: #32362b; font-size: 24px; font-weight: 600; }}
        QLabel#secondary {{ color: #786f59; font-size: 13px; }}
        QLabel#emptyLabel {{ color: #887d64; font-size: 14px; }}
        QLabel[completed="true"] {{ color: #817963; }}
        QPushButton {{
            background: transparent; border: none;
            border-radius: 8px; padding: 9px 10px;
        }}
        QPushButton:hover {{ background: {colors['hover']}; }}
        QPushButton#dateButton {{
            background: {colors['soft']}; border: 1px solid {colors['border']};
        }}
        QPushButton#iconButton {{
            min-width: 31px; max-width: 31px; padding: 7px 3px; font-size: 18px;
        }}
        QPushButton#primaryButton {{
            background: #444c39; color: #fffbed; font-weight: 600;
        }}
        QPushButton#primaryButton:hover {{ background: #5b654d; }}
        QPushButton#primaryButton:disabled {{
            background: rgba(118, 109, 84, 45); color: #756d59;
        }}
        QProgressBar {{
            background: rgba(130, 116, 81, 34);
            border: none; border-radius: 2px;
        }}
        QProgressBar::chunk {{ background: #78885b; border-radius: 2px; }}
        QFrame#taskRow {{
            border: none; border-bottom: 1px solid rgba(137, 123, 90, 44);
        }}
        QMenu {{
            background: #fffaf0; border: 1px solid #d6cbb2;
            border-radius: 7px; padding: 5px;
        }}
        QMenu::item {{ padding: 7px 24px 7px 12px; border-radius: 5px; }}
        QMenu::item:selected {{ background: #e6dfca; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
        QScrollBar::handle:vertical {{
            background: rgba(105, 99, 79, 85);
            min-height: 26px; border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
