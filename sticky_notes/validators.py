"""任务日期和时间校验。"""

from datetime import date, datetime

from sticky_notes.models.task import REPEAT_RULES


def validate_task_date(task_date):
    """检查任意任务日期；读取历史任务时使用。"""
    if not isinstance(task_date, str):
        raise TypeError("任务日期必须是字符串")

    task_date = task_date.strip()
    try:
        selected_date = datetime.strptime(task_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            "请输入包含年份的有效日期，格式为 YYYY-MM-DD，例如 2026-09-07"
        ) from None

    normalized = selected_date.isoformat()
    if normalized != task_date:
        raise ValueError("任务日期必须使用 YYYY-MM-DD 格式")
    return normalized


def validate_new_task_date(task_date):
    """检查新增或编辑日期，并禁止写入过去日期。"""
    task_date = validate_task_date(task_date)
    if date.fromisoformat(task_date) < date.today():
        raise ValueError("不能向过去日期添加或修改任务")
    return task_date


def validate_time_range(start_time=None, end_time=None):
    """检查同一天内的可选时间段。"""
    if start_time is not None and not isinstance(start_time, str):
        raise TypeError("开始时间必须是字符串或 None")
    if end_time is not None and not isinstance(end_time, str):
        raise TypeError("结束时间必须是字符串或 None")

    # 【助手编写】统一处理未填写值。
    start_time = "" if start_time is None else start_time.strip()
    end_time = "" if end_time is None else end_time.strip()

    # 【周子编写，按审查建议修正】判断两项时间是否成对填写。
    if not start_time and not end_time:
        return None, None
    if start_time == "" or end_time == "":
        raise ValueError("开始时间和结束时间必须一起填写")

    try:
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
    except ValueError:
        raise ValueError("请输入有效时间，例如 09:30 或 14:00") from None

    # 【周子编写】检查结束时间是否晚于开始时间。
    if start >= end:
        raise ValueError("结束时间必须晚于开始时间")

    return start.strftime("%H:%M"), end.strftime("%H:%M")


def validate_repeat_rule(repeat_rule="none"):
    """检查重复规则，返回统一的小写英文值。"""
    if not isinstance(repeat_rule, str):
        raise TypeError("重复规则必须是字符串")
    repeat_rule = repeat_rule.strip().lower()
    if repeat_rule not in REPEAT_RULES:
        raise ValueError("重复规则只能是 none、daily、weekly 或 monthly")
    return repeat_rule
