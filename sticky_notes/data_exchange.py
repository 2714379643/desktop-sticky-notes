"""TXT 导入，以及 JSON、TXT、CSV 备份导出。"""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from sticky_notes.models.task import Task
from sticky_notes.storage import SCHEMA_VERSION, TaskStorage

TXT_HEADER = (
    "date|start_time|end_time|title|repeat|weekday|month_day|repeat_start|repeat_end"
)
V11_TXT_HEADER = "date|start_time|end_time|title|repeat|weekday|month_day"
LEGACY_TXT_HEADER = "date|start_time|end_time|title|repeat"
TXT_EXAMPLE = """# Desktop Sticky Notes 1.1 导入模板
# 日期|开始时间|结束时间|任务内容|重复规则|星期|每月日期|每日开始|每日结束
# 重复规则：none / daily / weekly / monthly
# 星期使用 1 到 7（星期一到星期日）；每月日期使用 1 到 31
# 每日开始、每日结束都可留空；旧版 5 字段和 7 字段模板仍可导入
date|start_time|end_time|title|repeat|weekday|month_day|repeat_start|repeat_end
2099-09-08|08:30|10:00|学习 Python|none||||
2099-09-09|||每日阅读|daily|||2099-09-12|2099-10-12
"""


def build_import_report(imported, skipped, errors):
    """返回成功数、跳过数和错误详情组成的多行文字。"""
    # 【周子编写，助手指导，审查通过】
    if type(imported) is not int or imported < 0:
        raise ValueError("导入数量必须是非负整数")
    if type(skipped) is not int or skipped < 0:
        raise ValueError("跳过数量必须是非负整数")

    message = f"成功导入 {imported} 条，跳过 {skipped} 条。"
    if not errors:
        return message
    return message + "\n\n" + "\n".join(errors)


@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def message(self):
        visible_errors = list(self.errors[:8])
        if len(self.errors) > 8:
            visible_errors.append("……其余错误已省略")
        return build_import_report(self.imported, self.skipped, visible_errors)


def import_txt(path, task_service):
    """按固定竖线模板导入，错误行跳过并汇总。"""
    path = Path(path)
    result = ImportResult()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if (
                not line
                or line.startswith("#")
                or line.lower() in (TXT_HEADER, V11_TXT_HEADER, LEGACY_TXT_HEADER)
            ):
                continue
            try:
                fields = next(csv.reader([line], delimiter="|"))
                if len(fields) not in (5, 7, 9):
                    raise ValueError("必须包含 9 个字段（旧版 5、7 字段也兼容）")
                values = [item.strip() for item in fields]
                task_date, start, end, title, repeat = values[:5]
                weekday_text = values[5] if len(values) >= 7 else ""
                monthday_text = values[6] if len(values) >= 7 else ""
                repeat_start = values[7] if len(values) == 9 else ""
                repeat_end = values[8] if len(values) == 9 else ""
                repeat_weekday = int(weekday_text) - 1 if weekday_text else None
                repeat_monthday = int(monthday_text) if monthday_text else None
                task_service.add_task(
                    title,
                    task_date,
                    start or None,
                    end or None,
                    repeat or "none",
                    repeat_weekday,
                    repeat_monthday,
                    repeat_start or None,
                    repeat_end or None,
                )
                result.imported += 1
            except (TypeError, ValueError) as error:
                result.skipped += 1
                result.errors.append(f"第 {line_number} 行：{error}")
    return result


def import_json(path, task_service):
    """合并导入 1.0 至当前版本 JSON；只导入任务，不覆盖外观设置。"""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("JSON 最外层必须是对象")
    version = payload.get("schema_version", 1)
    if version not in (1, 2, 3, SCHEMA_VERSION):
        raise ValueError("这个 JSON 版本暂不支持")
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list):
        raise ValueError("JSON 中缺少 tasks 列表")

    result = ImportResult()
    known_ids = {task.task_id for task in task_service.tasks}
    validator = TaskStorage._validate_task_item
    for index, item in enumerate(raw_tasks, start=1):
        try:
            validator(item)
            task = Task.from_dict(item)
            if task.task_id in known_ids:
                result.skipped += 1
                result.errors.append(f"第 {index} 条：任务已存在")
                continue
            task_service.tasks.append(task)
            known_ids.add(task.task_id)
            result.imported += 1
        except (KeyError, TypeError, ValueError) as error:
            result.skipped += 1
            result.errors.append(f"第 {index} 条：{error}")
    return result


def export_json(path, tasks, settings):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tasks": [task.to_dict() for task in tasks],
        "settings": dict(settings),
    }
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export_txt(path, tasks):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
        file.write("# Desktop Sticky Notes 1.1\n")
        file.write(TXT_HEADER + "\n")
        writer = csv.writer(file, delimiter="|", lineterminator="\n")
        for task in tasks:
            if task.cancelled:
                continue
            writer.writerow(
                [
                    task.task_date,
                    task.start_time or "",
                    task.end_time or "",
                    task.title,
                    task.repeat_rule,
                    task.repeat_weekday + 1 if task.repeat_weekday is not None else "",
                    task.repeat_monthday or "",
                    task.recurrence_start_date or "",
                    task.recurrence_end_date or "",
                ]
            )


def export_csv(path, tasks):
    fields = [
        "task_id",
        "date",
        "start_time",
        "end_time",
        "title",
        "completed",
        "repeat",
        "weekday",
        "month_day",
        "repeat_start",
        "repeat_end",
    ]
    with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for task in tasks:
            if task.cancelled:
                continue
            writer.writerow(
                {
                    "task_id": task.task_id,
                    "date": task.task_date,
                    "start_time": task.start_time or "",
                    "end_time": task.end_time or "",
                    "title": task.title,
                    "completed": task.completed,
                    "repeat": task.repeat_rule,
                    "weekday": (
                        task.repeat_weekday + 1
                        if task.repeat_weekday is not None
                        else ""
                    ),
                    "month_day": task.repeat_monthday or "",
                    "repeat_start": task.recurrence_start_date or "",
                    "repeat_end": task.recurrence_end_date or "",
                }
            )
