"""任务与设置的 JSON 保存、读取和备份。"""

import json
import os
import shutil
import sys
from pathlib import Path

from sticky_notes.models.task import Task
from sticky_notes.validators import validate_task_date, validate_time_range

SCHEMA_VERSION = 4

DEFAULT_SETTINGS = {
    "theme": "雾光玻璃",
    "font_size": 15,
    "stay_on_bottom": True,
    "close_to_tray": True,
    "allow_early_completion": True,
    "window_width": 490,
    "window_height": 710,
    "window_x": None,
    "window_y": None,
}


class StorageError(Exception):
    """数据无法安全读取或保存时抛出的统一异常。"""


class TaskStorage:
    """使用临时文件原子保存，并保留上一份有效备份。"""

    def __init__(self, data_path=None):
        self.data_path = Path(data_path or self.default_data_path())
        self.backup_path = self.data_path.with_suffix(".json.bak")
        self.temp_path = self.data_path.with_suffix(".json.tmp")

    @staticmethod
    def default_data_path():
        """源码运行放在项目旁；打包后放在 EXE 旁。"""
        if getattr(sys, "frozen", False):
            app_directory = Path(sys.executable).resolve().parent
        else:
            app_directory = Path(__file__).resolve().parents[1]
        return app_directory / "msgs" / "data.json"

    def migrate_legacy_data(self):
        """新目录为空时复制一份旧版数据，不删除旧文件。"""
        if self.data_path.exists():
            return None

        candidates = []
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "DesktopStickyNotes" / "data.json")
        candidates.extend(
            [
                self.data_path.parent.parent.parent / "msgs" / "data.json",
                Path(r"D:\Software\desktop-sticky-notes\msgs\data.json"),
                Path(r"D:\Desktop\desktop-sticky-notes\msgs\data.json"),
            ]
        )

        for candidate in candidates:
            try:
                if candidate.resolve() == self.data_path.resolve():
                    continue
                if candidate.is_file() and self._file_is_valid(candidate):
                    self.data_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(candidate, self.data_path)
                    return candidate
            except OSError:
                continue
        return None

    def save(self, tasks, settings):
        """安全保存全部任务和设置。"""
        if not isinstance(tasks, list):
            raise TypeError("任务集合必须是列表")
        if not isinstance(settings, dict):
            raise TypeError("设置数据必须是字典")
        if not all(isinstance(task, Task) for task in tasks):
            raise TypeError("任务列表中只能存放 Task 对象")

        payload = {
            "schema_version": SCHEMA_VERSION,
            "tasks": [task.to_dict() for task in tasks],
            "settings": self._merge_settings(settings),
        }
        self._validate_payload(payload)

        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(payload, ensure_ascii=False, indent=2)

            with self.temp_path.open("w", encoding="utf-8") as file:
                file.write(text)
                file.flush()
                os.fsync(file.fileno())

            # 旧文件有效时才覆盖备份，避免把损坏文件复制到备份。
            if self.data_path.exists() and self._file_is_valid(self.data_path):
                shutil.copy2(self.data_path, self.backup_path)

            os.replace(self.temp_path, self.data_path)
        except OSError as error:
            raise StorageError(f"保存任务数据失败：{error}") from error
        finally:
            try:
                self.temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def load(self):
        """返回 (Task 列表, 设置字典, 是否从备份恢复)。"""
        self.migrate_legacy_data()
        if not self.data_path.exists():
            return [], DEFAULT_SETTINGS.copy(), False

        try:
            return (*self._load_path(self.data_path), False)
        except StorageError as main_error:
            if not self.backup_path.exists():
                raise StorageError("任务数据无法读取，并且没有可用备份") from main_error
            try:
                return (*self._load_path(self.backup_path), True)
            except StorageError as backup_error:
                raise StorageError("主数据文件和备份文件都无法读取") from backup_error

    def _load_path(self, path):
        payload = self._read_payload(path)
        return self._validate_payload(payload)

    @staticmethod
    def _read_payload(path):
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise StorageError(f"无法读取数据文件：{path}") from error

    def _file_is_valid(self, path):
        try:
            self._load_path(path)
            return True
        except StorageError:
            return False

    def _validate_payload(self, payload):
        if not isinstance(payload, dict):
            raise StorageError("数据文件最外层必须是字典")
        schema_version = payload.get("schema_version")
        if schema_version not in (1, 2, 3, SCHEMA_VERSION):
            raise StorageError("数据文件版本不受支持")

        raw_tasks = payload.get("tasks")
        raw_settings = payload.get("settings")
        if not isinstance(raw_tasks, list):
            raise StorageError("数据文件中的 tasks 必须是列表")
        if not isinstance(raw_settings, dict):
            raise StorageError("数据文件中的 settings 必须是字典")

        tasks = []
        task_ids = set()
        for index, item in enumerate(raw_tasks, start=1):
            try:
                self._validate_task_item(item)
                task = Task.from_dict(item)
                if task.task_id in task_ids:
                    raise ValueError("任务 ID 重复")
                task_ids.add(task.task_id)
                tasks.append(task)
            except (KeyError, TypeError, ValueError) as error:
                raise StorageError(f"第 {index} 条任务数据无效：{error}") from error

        return tasks, self._merge_settings(raw_settings)

    @staticmethod
    def _validate_task_item(item):
        if not isinstance(item, dict):
            raise TypeError("任务数据必须是字典")
        if not isinstance(item["title"], str):
            raise TypeError("任务内容必须是字符串")
        if not isinstance(item["completed"], bool):
            raise TypeError("完成状态必须是布尔值")

        task_id = item.get("task_id")
        if task_id is not None and (
            not isinstance(task_id, str) or not task_id.strip()
        ):
            raise TypeError("任务 ID 必须是非空字符串")

        validate_task_date(item["task_date"])
        validate_time_range(item["start_time"], item["end_time"])
        repeat_rule = item.get("repeat_rule", "none")
        if repeat_rule not in ("none", "daily", "weekly", "monthly"):
            raise ValueError("重复规则无效")
        repeat_weekday = item.get("repeat_weekday")
        if repeat_weekday is not None and (
            isinstance(repeat_weekday, bool)
            or not isinstance(repeat_weekday, int)
            or not 0 <= repeat_weekday <= 6
        ):
            raise ValueError("每周重复日期必须是 0 到 6")
        repeat_monthday = item.get("repeat_monthday")
        if repeat_monthday is not None and (
            isinstance(repeat_monthday, bool)
            or not isinstance(repeat_monthday, int)
            or not 1 <= repeat_monthday <= 31
        ):
            raise ValueError("每月重复日期必须是 1 到 31")
        origin_date = item.get("recurrence_origin_date", item["task_date"])
        validate_task_date(origin_date)
        repeat_start = item.get("recurrence_start_date")
        repeat_end = item.get("recurrence_end_date")
        if repeat_start is not None:
            validate_task_date(repeat_start)
        if repeat_end is not None:
            validate_task_date(repeat_end)
        if not isinstance(item.get("generated", False), bool):
            raise TypeError("generated 必须是布尔值")
        if not isinstance(item.get("cancelled", False), bool):
            raise TypeError("cancelled 必须是布尔值")

    @staticmethod
    def _merge_settings(settings):
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)

        legacy_themes = {
            "奶油纸": "日式庭院纸",
            "鼠尾草": "雾光玻璃",
            "浅玫瑰": "马卡龙晨光",
        }
        merged["theme"] = legacy_themes.get(merged["theme"], merged["theme"])
        valid_themes = (
            "雾光玻璃",
            "日式庭院纸",
            "黑金夜幕",
            "马卡龙晨光",
            "水墨留白",
            "瑞士极简",
            "森林手账",
            "伊蕾娜旅记",
        )
        if merged["theme"] not in valid_themes:
            merged["theme"] = DEFAULT_SETTINGS["theme"]

        font_size = merged["font_size"]
        if isinstance(font_size, bool) or not isinstance(font_size, int):
            font_size = DEFAULT_SETTINGS["font_size"]
        merged["font_size"] = max(12, min(font_size, 22))

        if not isinstance(merged["stay_on_bottom"], bool):
            merged["stay_on_bottom"] = DEFAULT_SETTINGS["stay_on_bottom"]
        if not isinstance(merged["close_to_tray"], bool):
            merged["close_to_tray"] = DEFAULT_SETTINGS["close_to_tray"]
        if not isinstance(merged["allow_early_completion"], bool):
            merged["allow_early_completion"] = DEFAULT_SETTINGS[
                "allow_early_completion"
            ]
        # 1.1 改为由 quotes 包提供每日文案，移除旧版手动输入设置。
        merged.pop("quote_text", None)

        for key in ("window_width", "window_height"):
            value = merged[key]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                merged[key] = DEFAULT_SETTINGS[key]

        for key in ("window_x", "window_y"):
            value = merged[key]
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                merged[key] = None
        return merged
