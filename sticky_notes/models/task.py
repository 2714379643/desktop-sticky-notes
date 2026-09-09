"""单条待办任务的数据模型。"""

from datetime import date
from uuid import uuid4

REPEAT_RULES = ("none", "daily", "weekly", "monthly")


class Task:
    """保存一条任务的内容、日期、可选时间和完成状态。"""

    def __init__(
        self,
        title,
        task_date,
        start_time=None,
        end_time=None,
        task_id=None,
        completed=False,
        repeat_rule="none",
        series_id=None,
        recurrence_origin_date=None,
        repeat_weekday=None,
        repeat_monthday=None,
        recurrence_start_date=None,
        recurrence_end_date=None,
        generated=False,
        cancelled=False,
    ):
        # 【助手补充】稳定 ID 用于编辑、删除和跨次启动定位同一任务。
        if task_id is None:
            task_id = uuid4().hex
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("任务 ID 不能为空")

        self.task_id = task_id.strip()
        self.set_title(title)
        self.task_date = task_date
        self.start_time = start_time
        self.end_time = end_time
        if not isinstance(completed, bool):
            raise TypeError("完成状态必须是布尔值")
        if repeat_rule not in REPEAT_RULES:
            raise ValueError("重复规则必须是 none、daily、weekly 或 monthly")
        if not isinstance(generated, bool):
            raise TypeError("generated 必须是布尔值")
        if not isinstance(cancelled, bool):
            raise TypeError("cancelled 必须是布尔值")

        if series_id is not None and (
            not isinstance(series_id, str) or not series_id.strip()
        ):
            raise TypeError("series_id 必须是非空字符串")

        self.completed = completed
        self.repeat_rule = repeat_rule
        self.series_id = (series_id or self.task_id).strip()
        self.recurrence_origin_date = recurrence_origin_date or task_date
        self.recurrence_start_date = recurrence_start_date
        self.recurrence_end_date = recurrence_end_date
        self._validate_recurrence_range()
        self.repeat_weekday, self.repeat_monthday = self._repeat_options(
            repeat_rule,
            self.recurrence_origin_date,
            repeat_weekday,
            repeat_monthday,
        )
        self.generated = generated
        self.cancelled = cancelled

    def _validate_recurrence_range(self):
        """检查可选重复区间；空开始日期表示从首次任务日期开始。"""
        try:
            origin = date.fromisoformat(self.recurrence_origin_date)
            start = (
                date.fromisoformat(self.recurrence_start_date)
                if self.recurrence_start_date is not None
                else origin
            )
            end = (
                date.fromisoformat(self.recurrence_end_date)
                if self.recurrence_end_date is not None
                else None
            )
        except (TypeError, ValueError):
            raise ValueError("重复任务日期必须使用 YYYY-MM-DD 格式") from None
        if self.repeat_rule == "none" and (
            self.recurrence_start_date is not None
            or self.recurrence_end_date is not None
        ):
            raise ValueError("不重复任务不能设置重复区间")
        if end is not None and end < start:
            raise ValueError("重复结束日期不能早于开始日期")

    @staticmethod
    def _repeat_options(
        repeat_rule,
        origin_date,
        repeat_weekday=None,
        repeat_monthday=None,
    ):
        """统一重复参数；旧数据缺少参数时从起始日期推算。"""
        if repeat_rule == "weekly":
            if repeat_weekday is None:
                repeat_weekday = date.fromisoformat(origin_date).weekday()
            if (
                isinstance(repeat_weekday, bool)
                or not isinstance(repeat_weekday, int)
                or not 0 <= repeat_weekday <= 6
            ):
                raise ValueError("每周重复日期必须是星期一到星期日")
            return repeat_weekday, None

        if repeat_rule == "monthly":
            if repeat_monthday is None:
                repeat_monthday = date.fromisoformat(origin_date).day
            if (
                isinstance(repeat_monthday, bool)
                or not isinstance(repeat_monthday, int)
                or not 1 <= repeat_monthday <= 31
            ):
                raise ValueError("每月重复日期必须是 1 到 31 号")
            return None, repeat_monthday

        return None, None

    def set_title(self, title):
        # 【周子编写，审查后调整】检查并保存任务标题。
        if not isinstance(title, str):
            raise TypeError("任务内容必须是字符串")
        title = title.strip()
        if title == "":
            raise ValueError("任务内容不能为空")
        self.title = title

    def toggle_completed(self):
        # 【周子编写，审查后简化】切换任务的完成状态。
        self.completed = not self.completed

    def to_dict(self):
        # 【周子编写，审查后修正字段名】完成了最初的五个任务字段。
        # 【助手补充】加入 task_id，使任务重启后仍可被准确定位。
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_date": self.task_date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "completed": self.completed,
            "repeat_rule": self.repeat_rule,
            "series_id": self.series_id,
            "recurrence_origin_date": self.recurrence_origin_date,
            "repeat_weekday": self.repeat_weekday,
            "repeat_monthday": self.repeat_monthday,
            "recurrence_start_date": self.recurrence_start_date,
            "recurrence_end_date": self.recurrence_end_date,
            "generated": self.generated,
            "cancelled": self.cancelled,
        }

    @classmethod
    def from_dict(cls, data):
        # 【助手编写，周子参与前置尝试】把保存的字典恢复成 Task。
        if not isinstance(data, dict):
            raise TypeError("任务数据必须是字典")
        task = cls(
            title=data["title"],
            task_date=data["task_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            # 兼容早期没有 ID 的数据，首次自动保存后会补上 ID。
            task_id=data.get("task_id"),
            completed=data["completed"],
            repeat_rule=data.get("repeat_rule", "none"),
            series_id=data.get("series_id"),
            recurrence_origin_date=data.get("recurrence_origin_date"),
            repeat_weekday=data.get("repeat_weekday"),
            repeat_monthday=data.get("repeat_monthday"),
            recurrence_start_date=data.get("recurrence_start_date"),
            recurrence_end_date=data.get("recurrence_end_date"),
            generated=data.get("generated", False),
            cancelled=data.get("cancelled", False),
        )
        return task
