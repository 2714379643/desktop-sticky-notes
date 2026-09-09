"""从同级 TXT 文件读取并整理每日励志文案。"""

import sys
from pathlib import Path

from sticky_notes.quote_formatter import normalize_quote

QUOTE_FILE_NAME = "励志语录100条.txt"


def _parse_quote_blocks(text):
    """以空行分隔文案，每条文案内部允许包含一至三行。"""
    quotes = []
    current_quote = []

    for raw_line in text.splitlines():
        cleaned_line = raw_line.strip()
        if not cleaned_line:
            if current_quote:
                quotes.append("\n".join(current_quote))
                current_quote = []
            continue
        current_quote.append(cleaned_line)
        if len(current_quote) > 3:
            raise ValueError("每条文案最多三行，请在不同文案之间保留一个空行")

    if current_quote:
        quotes.append("\n".join(current_quote))

    return quotes


def quote_file_path():
    """源码读取 content.py 同级文件；EXE 优先读取程序旁的可编辑文件。"""
    package_file = Path(__file__).resolve().with_name(QUOTE_FILE_NAME)
    if getattr(sys, "frozen", False):
        external_file = Path(sys.executable).resolve().with_name(QUOTE_FILE_NAME)
        if external_file.is_file():
            return external_file
    return package_file


def load_quotes(file_path=None):
    """读取 UTF-8 TXT，返回整理后的文案列表。"""
    path = Path(file_path) if file_path is not None else quote_file_path()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"没有找到励志文案文件：{path}") from error
    except UnicodeDecodeError as error:
        raise ValueError("励志文案文件必须使用 UTF-8 编码") from error

    quotes = [
        normalize_quote(quote)
        for quote in _parse_quote_blocks(text)
    ]
    if not quotes:
        raise ValueError("励志文案文件不能为空")
    if len(quotes) != len(set(quotes)):
        raise ValueError("励志文案文件中存在完全重复的内容")
    return quotes


QUOTES = load_quotes()
