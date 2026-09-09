"""v1.1 的主题色、玻璃质感与统一控件样式。"""


THEMES = {
    "雾光玻璃": {
        "mode": "glass", "motif": "none",
        "surface": (226, 240, 249, 40), "backdrop": (205, 229, 244, 32),
        "edge": (255, 255, 255, 205), "shadow": (28, 64, 91, 56),
        "border": "rgba(255, 255, 255, 205)", "text": "#17324c",
        "muted": "#49677c", "accent": "#5d7ff2", "accent_hover": "#496de5",
        "soft": "rgba(248, 253, 255, 84)", "quote_soft": "rgba(244, 251, 255, 62)",
        "quote_border": "rgba(255, 255, 255, 190)", "hover": "rgba(255, 255, 255, 110)",
        "divider": "rgba(45, 73, 82, 35)", "danger": "#a94e55",
        "highlight_alpha": 58, "quote_font": '"Segoe UI", "Microsoft YaHei UI"',
        "progress_track": "rgba(44, 77, 104, 92)", "progress_border": "rgba(255,255,255,222)",
        "dialog_bg": "rgba(211, 230, 245, 196)", "input_bg": "rgba(255,255,255,126)",
    },
    "日式庭院纸": {
        "mode": "solid", "motif": "branch",
        "surface": (250, 243, 224, 255), "backdrop": (250, 243, 224, 0),
        "edge": (139, 117, 82, 70), "shadow": (73, 63, 42, 45),
        "border": "rgba(139, 117, 82, 95)", "text": "#38382f",
        "muted": "#786f5e", "accent": "#61745a", "accent_hover": "#53674c",
        "soft": "rgba(255, 255, 255, 112)", "quote_soft": "rgba(255, 255, 255, 74)",
        "quote_border": "rgba(139, 117, 82, 48)", "hover": "rgba(111, 132, 92, 35)",
        "divider": "rgba(122, 105, 74, 43)", "danger": "#9d493e",
        "highlight_alpha": 0, "quote_font": '"Georgia", "Microsoft YaHei UI"',
        "progress_track": "rgba(111,95,64,42)", "progress_border": "rgba(139,117,82,70)",
        "dialog_bg": "#f7f0df", "input_bg": "#fffaf0",
    },
    "黑金夜幕": {
        "mode": "solid", "motif": "night",
        "surface": (24, 27, 31, 255), "backdrop": (24, 27, 31, 0),
        "edge": (222, 193, 125, 82), "shadow": (0, 0, 0, 72),
        "border": "rgba(222, 193, 125, 95)", "text": "#f3ead5",
        "muted": "#b6ab95", "accent": "#c6a15b", "accent_hover": "#d5b46f",
        "accent_text": "#2b210d",
        "soft": "rgba(255, 255, 255, 18)", "quote_soft": "rgba(255, 255, 255, 14)",
        "quote_border": "rgba(222, 193, 125, 72)", "hover": "rgba(220, 183, 108, 30)",
        "divider": "rgba(224, 195, 130, 38)", "danger": "#db7d70",
        "highlight_alpha": 0, "quote_font": '"Segoe UI", "Microsoft YaHei UI"',
        "progress_track": "rgba(222,193,125,25)", "progress_border": "rgba(222,193,125,86)",
        "dialog_bg": "#1c1f23", "input_bg": "#292c31",
    },
    "马卡龙晨光": {
        "mode": "solid", "motif": "clouds",
        "surface": (251, 237, 244, 255), "backdrop": (251, 237, 244, 0),
        "edge": (255, 255, 255, 118), "shadow": (100, 71, 104, 40),
        "border": "rgba(255, 255, 255, 178)", "text": "#463d4e",
        "muted": "#85758c", "accent": "#9a78ad", "accent_hover": "#88659e",
        "soft": "rgba(255, 255, 255, 105)", "quote_soft": "rgba(255, 255, 255, 80)",
        "quote_border": "rgba(255, 255, 255, 140)", "hover": "rgba(173, 133, 194, 32)",
        "divider": "rgba(120, 84, 135, 32)", "danger": "#ad5a6f",
        "highlight_alpha": 0, "quote_font": '"Segoe UI", "Microsoft YaHei UI"',
        "progress_track": "rgba(111,74,125,28)", "progress_border": "rgba(255,255,255,158)",
        "dialog_bg": "#faedf4", "input_bg": "#fff9fc",
    },
    "水墨留白": {
        "mode": "solid", "motif": "ink",
        "surface": (242, 242, 236, 255), "backdrop": (242, 242, 236, 0),
        "edge": (66, 70, 65, 60), "shadow": (37, 45, 42, 40),
        "border": "rgba(66, 70, 65, 72)", "text": "#272b29",
        "muted": "#6d736f", "accent": "#4f6760", "accent_hover": "#405851",
        "soft": "rgba(255, 255, 255, 105)", "quote_soft": "rgba(255, 255, 255, 64)",
        "quote_border": "rgba(66, 70, 65, 34)", "hover": "rgba(51, 78, 70, 27)",
        "divider": "rgba(45, 53, 49, 34)", "danger": "#95544c",
        "highlight_alpha": 0, "quote_font": '"Georgia", "Microsoft YaHei UI"',
        "progress_track": "rgba(45,53,49,30)", "progress_border": "rgba(66,70,65,60)",
        "dialog_bg": "#f1f1eb", "input_bg": "#fbfbf7",
    },
    "瑞士极简": {
        "mode": "solid", "motif": "swiss",
        "surface": (249, 249, 247, 255), "backdrop": (249, 249, 247, 0),
        "edge": (20, 23, 25, 48), "shadow": (25, 28, 30, 36),
        "border": "rgba(20, 23, 25, 55)", "text": "#17191b",
        "muted": "#72767a", "accent": "#d94b45", "accent_hover": "#bd3f3a",
        "soft": "rgba(20, 23, 25, 10)", "quote_soft": "rgba(20, 23, 25, 7)",
        "quote_border": "rgba(20, 23, 25, 42)", "hover": "rgba(217, 75, 69, 18)",
        "divider": "rgba(20, 23, 25, 34)", "danger": "#ba3732",
        "highlight_alpha": 0, "quote_font": '"Segoe UI", "Microsoft YaHei UI"',
        "progress_track": "rgba(20,23,25,22)", "progress_border": "rgba(20,23,25,50)",
        "dialog_bg": "#f7f7f5", "input_bg": "#ffffff",
    },
    "森林手账": {
        "mode": "solid", "motif": "forest",
        "surface": (229, 235, 218, 255), "backdrop": (229, 235, 218, 0),
        "edge": (70, 90, 60, 72), "shadow": (40, 62, 35, 44),
        "border": "rgba(70, 90, 60, 88)", "text": "#2f3b2e",
        "muted": "#667462", "accent": "#567151", "accent_hover": "#465f42",
        "soft": "rgba(255, 255, 255, 80)", "quote_soft": "rgba(255, 255, 255, 58)",
        "quote_border": "rgba(70, 90, 60, 54)", "hover": "rgba(72, 102, 67, 28)",
        "divider": "rgba(60, 80, 55, 40)", "danger": "#9c5448",
        "highlight_alpha": 0, "quote_font": '"Segoe UI", "Microsoft YaHei UI"',
        "progress_track": "rgba(60,80,55,34)", "progress_border": "rgba(70,90,60,65)",
        "dialog_bg": "#e8edde", "input_bg": "#f4f7ee",
    },
    "伊蕾娜旅记": {
        "mode": "solid", "motif": "elaina",
        "surface": (43, 38, 61, 255), "backdrop": (43, 38, 61, 0),
        "edge": (213, 199, 231, 108), "shadow": (13, 9, 24, 88),
        "border": "rgba(213, 199, 231, 115)", "text": "#f4effa",
        "muted": "#c3b8d4", "accent": "#8d6ab8", "accent_hover": "#a17dca",
        "soft": "rgba(239, 226, 255, 18)", "quote_soft": "rgba(232, 216, 255, 16)",
        "quote_border": "rgba(213, 199, 231, 74)", "hover": "rgba(197, 167, 231, 32)",
        "divider": "rgba(213, 199, 231, 34)", "danger": "#ef8992",
        "highlight_alpha": 0, "quote_font": '"Georgia", "Microsoft YaHei UI"',
        "progress_track": "rgba(226,211,244,25)", "progress_border": "rgba(213,199,231,95)",
        "dialog_bg": "#2e2941", "input_bg": "#3c3651",
    },
}


def dialog_style(theme_name="雾光玻璃", font_size=14):
    colors = THEMES.get(theme_name, THEMES["雾光玻璃"])
    accent_text = colors.get("accent_text", "white")
    return f"""
        QDialog {{ background: transparent; }}
        QWidget {{ color: {colors['text']}; font-family: "Microsoft YaHei UI", "Noto Sans CJK SC"; font-size: {font_size}px; }}
        QFrame#dialogSurface {{ background: {colors['dialog_bg']}; border: 1px solid {colors['border']}; border-radius: 22px; }}
        QLabel#heading {{ color: {colors['text']}; font-size: 22px; font-weight: 650; }}
        QLabel#secondary {{ color: {colors['muted']}; font-size: 13px; }}
        QLabel#fieldLabel {{ color: {colors['text']}; font-weight: 600; }}
        QLabel#error {{ color: {colors['danger']}; background: {colors['soft']}; border-radius: 9px; padding: 9px 11px; }}
        QFrame#form, QFrame#section, QFrame#calendarCard {{ background: {colors['soft']}; border: 1px solid {colors['border']}; border-radius: 14px; }}
        QFrame#dialogBody {{ background: transparent; border: none; }}
        QLineEdit, QDateEdit, QComboBox, QSpinBox, QTextEdit, QListWidget, QPushButton#dateButton {{ background: {colors['input_bg']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 9px; padding: 7px 9px; selection-background-color: {colors['accent']}; }}
        QLineEdit:disabled, QDateEdit:disabled, QComboBox:disabled, QPushButton#dateButton:disabled {{ color: {colors['muted']}; background: {colors['soft']}; }}
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QListWidget:focus {{ border: 1px solid {colors['accent']}; }}
        QComboBox QAbstractItemView {{ background: {colors['input_bg']}; color: {colors['text']}; border: 1px solid {colors['border']}; selection-background-color: {colors['accent']}; selection-color: {accent_text}; outline: none; padding: 4px; }}
        QComboBox QAbstractItemView::item {{ color: {colors['text']}; background: {colors['input_bg']}; min-height: 30px; padding: 4px 8px; }}
        QComboBox QAbstractItemView::item:selected {{ color: {accent_text}; background: {colors['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox#themeCombo {{ padding-right: 38px; min-height: 22px; }}
        QComboBox#themeCombo::drop-down {{ width: 34px; border: none; }}
        QComboBox#themeCombo::down-arrow {{ image: none; width: 0px; height: 0px; }}
        QPushButton#circleControl {{ min-width: 0px; min-height: 0px; padding: 0px; border: none; background: transparent; }}
        QListWidget::item {{ padding: 7px; border-radius: 6px; }}
        QListWidget::item:selected {{ background: {colors['accent']}; color: {accent_text}; }}
        QPushButton {{ min-height: 24px; color: {colors['text']}; background: {colors['soft']}; border: 1px solid {colors['border']}; border-radius: 9px; padding: 8px 15px; }}
        QPushButton:hover {{ background: {colors['hover']}; }}
        QPushButton#primaryButton {{ background: {colors['accent']}; color: {accent_text}; font-weight: 600; }}
        QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#dangerButton {{ background: {colors['danger']}; color: white; font-weight: 600; }}
        QPushButton#dialogClose, QPushButton#calendarArrow {{ min-width: 36px; min-height: 36px; max-width: 36px; max-height: 36px; padding: 0px; border-radius: 18px; background: {colors['soft']}; border: 1px solid {colors['border']}; font-size: 22px; }}
        QPushButton#dialogClose:hover, QPushButton#calendarArrow:hover {{ background: {colors['hover']}; border-color: {colors['accent']}; }}
        QLabel#calendarMonth {{ color: {colors['text']}; font-size: 18px; font-weight: 650; }}
        QPushButton#dataButton {{ text-align: left; background: {colors['soft']}; }}
        QPushButton#dataButton:hover {{ background: {colors['hover']}; }}
        QFrame#fontPicker {{ background: {colors['input_bg']}; border: 1px solid {colors['border']}; border-radius: 9px; }}
        QFrame#fontPicker QLabel {{ border: none; background: transparent; font-weight: 600; }}
        QPushButton#fontStep {{ min-height: 0px; background: transparent; border: none; border-radius: 7px; padding: 0px; font-size: 20px; font-weight: 600; }}
        QPushButton#fontStep:hover {{ background: {colors['hover']}; color: {colors['accent']}; }}
        QPushButton#fontStep:disabled {{ color: {colors['muted']}; }}
        QRadioButton#deleteOption {{ background: {colors['input_bg']}; border: 1px solid {colors['border']}; border-radius: 13px; padding: 15px 16px; spacing: 12px; font-weight: 600; }}
        QRadioButton#deleteOption:hover {{ border-color: {colors['accent']}; background: {colors['hover']}; }}
        QRadioButton#deleteOption::indicator {{ width: 20px; height: 20px; border-radius: 10px; border: 1px solid {colors['accent']}; background: transparent; }}
        QRadioButton#deleteOption::indicator:checked {{ background: {colors['accent']}; border: 4px solid {colors['input_bg']}; }}
        QCheckBox {{ spacing: 9px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 10px; border: 1px solid {colors['border']}; background: {colors['input_bg']}; }}
        QCheckBox::indicator:checked {{ background: {colors['accent']}; border: 4px solid {colors['input_bg']}; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; }}
        QScrollBar::handle:vertical {{ background: rgba(75, 91, 98, 80); min-height: 28px; border-radius: 4px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """


def compact_calendar_style(theme_name):
    """主窗口月历沿用当前主题的强调色。"""
    colors = THEMES.get(theme_name, THEMES["雾光玻璃"])
    accent_text = colors.get("accent_text", "white")
    return f"""
        QLabel#calendarWeekday {{
            color: {colors['muted']}; font-size: 12px; font-weight: 600;
            background: transparent; border: none;
        }}
        QPushButton#calendarDay {{
            min-width: 0px; min-height: 34px; max-height: 34px;
            padding: 0px; border: 1px solid transparent; border-radius: 17px;
            background: transparent; color: {colors['text']}; font-size: 14px;
        }}
        QPushButton#calendarDay:hover {{
            background: {colors['hover']}; border-color: {colors['border']};
        }}
        QPushButton#calendarDay[outside="true"] {{ color: {colors['muted']}; }}
        QPushButton#calendarDay:disabled {{ color: {colors['divider']}; }}
        QPushButton#calendarDay[today="true"] {{
            border: 1px solid {colors['accent']}; color: {colors['accent']};
        }}
        QPushButton#calendarDay[selected="true"] {{
            background: {colors['accent']}; color: {accent_text};
            border: 1px solid {colors['accent']}; font-weight: 700;
        }}
    """


def note_style(theme_name, font_size, scale=1.0):
    colors = THEMES.get(theme_name, THEMES["雾光玻璃"])
    accent_text = colors.get("accent_text", "white")
    body_size = max(12, round(font_size * scale))
    heading_size = max(22, round(27 * scale))
    small_size = max(11, round(12 * scale))
    radius = max(9, round(12 * scale))
    pad_y = max(6, round(7 * scale))
    return f"""
        QWidget {{ color: {colors['text']}; font-family: "Microsoft YaHei UI", "Segoe UI", "Noto Sans CJK SC"; font-size: {body_size}px; }}
        QFrame#paper {{ background: transparent; border: none; }}
        QLabel, QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
        QLabel#overline {{ color: {colors['muted']}; font-size: {small_size}px; font-weight: 600; letter-spacing: 1px; }}
        QLabel#heading {{ color: {colors['text']}; font-size: {heading_size}px; font-weight: 650; }}
        QLabel#secondary {{ color: {colors['muted']}; font-size: {small_size}px; }}
        QLabel#emptyLabel {{ color: {colors['muted']}; font-size: {body_size}px; }}
        QLabel[completed="true"] {{ color: {colors['muted']}; }}
        QPushButton {{ background: transparent; border: none; border-radius: {radius}px; padding: {pad_y}px {max(8, round(11 * scale))}px; }}
        QPushButton:hover {{ background: {colors['hover']}; }}
        QPushButton#glassButton {{ background: {colors['soft']}; border: 1px solid {colors['border']}; }}
        QPushButton#iconButton {{ min-width: {max(28, round(32 * scale))}px; max-width: {max(28, round(32 * scale))}px; padding: {max(5, round(6 * scale))}px 2px; background: {colors['soft']}; border: 1px solid {colors['border']}; border-radius: {max(15, round(18 * scale))}px; }}
        QPushButton#iconButton:hover {{ background: {colors['hover']}; border-color: {colors['accent']}; }}
        QPushButton#primaryButton {{ background: {colors['accent']}; color: {accent_text}; font-weight: 600; padding: {max(8, round(9 * scale))}px {max(13, round(17 * scale))}px; }}
        QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#primaryButton:disabled {{ background: rgba(110, 120, 122, 38); color: {colors['muted']}; }}
        QPushButton#roundAddButton {{
            background: transparent; border: none; padding: 0px;
        }}
        QPushButton#circleControl {{ min-width: 0px; min-height: 0px; padding: 0px; border: none; background: transparent; }}
        QProgressBar {{ background: {colors['progress_track']}; border: 1px solid {colors['progress_border']}; border-radius: 4px; }}
        QProgressBar::chunk {{ background: {colors['accent']}; border-radius: 3px; }}
        QFrame#headerDivider {{ background: {colors['divider']}; border: none; }}
        QFrame#taskRow {{ background: transparent; border: none; border-bottom: 1px solid {colors['divider']}; }}
        QFrame#quotePanel {{ background: {colors['quote_soft']}; border: 1px solid {colors['quote_border']}; border-radius: {max(12, round(15 * scale))}px; }}
        QScrollArea#quoteScroll, QLabel#quoteText {{ background: transparent; border: none; color: {colors['muted']}; }}
        QLabel#quoteText {{ font-family: {colors['quote_font']}; }}
        QMenu {{ background: {colors['dialog_bg']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 5px; }}
        QMenu::item {{ padding: 7px 24px 7px 12px; border-radius: 6px; }}
        QMenu::item:selected {{ background: {colors['hover']}; }}
        QScrollBar:vertical {{ background: transparent; width: 7px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: rgba(75, 91, 98, 70); min-height: 26px; border-radius: 3px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
