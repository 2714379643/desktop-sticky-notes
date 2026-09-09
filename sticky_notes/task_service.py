"""任务业务管理：创建、查询、重复生成、编辑与删除。"""

import calendar
from datetime import date, timedelta

from sticky_notes.models.task import Task
from sticky_notes.task_statistics import calculate_daily_summary
from sticky_notes.validators import (
    validate_new_task_date,
    validate_repeat_rule,
    validate_time_range,
)


class TaskService:
    def __init__(self, tasks=None):
        # 【周子编写，助手扩展】周子完成了实例空列表；现支持载入已有任务。
        if tasks is None:
            tasks = []
        if not isinstance(tasks, list) or not all(
            isinstance(task, Task) for task in tasks
        ):
            raise TypeError("tasks 必须是只包含 Task 对象的列表")
        self.tasks = list(tasks)

    def add_task(
        self,
        title,
        task_date,
        start_time=None,
        end_time=None,
        repeat_rule="none",
        repeat_weekday=None,
        repeat_monthday=None,
        recurrence_start_date=None,
        recurrence_end_date=None,
    ):
        """校验并添加任务，返回新建的 Task 对象。"""
        # 【周子编写，审查后修正】核心流程：校验、构造、追加并返回。
        task_date = validate_new_task_date(task_date)
        start_time, end_time = validate_time_range(start_time, end_time)
        repeat_rule = validate_repeat_rule(repeat_rule)
        recurrence_start_date, recurrence_end_date = self._validate_repeat_range(
            task_date,
            repeat_rule,
            recurrence_start_date,
            recurrence_end_date,
        )
        effective_date = self._first_occurrence(
            recurrence_start_date or task_date,
            repeat_rule,
            repeat_weekday,
            repeat_monthday,
        )
        task = Task(
            title,
            effective_date,
            start_time,
            end_time,
            repeat_rule=repeat_rule,
            recurrence_origin_date=effective_date,
            repeat_weekday=repeat_weekday,
            repeat_monthday=repeat_monthday,
            recurrence_start_date=recurrence_start_date,
            recurrence_end_date=recurrence_end_date,
        )
        self.tasks.append(task)
        return task

    def get_tasks_by_date(self, task_date):
        """返回指定日期的任务副列表，允许查询过去日期。"""
        # 【周子编写】遍历全部任务并筛选同一天的对象。
        query_result = []
        for task in self.tasks:
            if task.task_date == task_date and not task.cancelled:
                query_result.append(task)

        # 【助手补充】有时间的任务优先，并按开始时间排序；排序稳定。
        return sorted(
            query_result,
            key=lambda task: (task.start_time is None, task.start_time or ""),
        )

    def ensure_recurring_for_date(self, task_date):
        """按需生成某天的重复任务，返回新生成数量。"""
        target = date.fromisoformat(task_date)
        existing_keys = {(task.series_id, task.task_date) for task in self.tasks}
        origins = [
            task
            for task in self.tasks
            if task.repeat_rule != "none"
            and not task.generated
            and task.task_date == task.recurrence_origin_date
        ]
        generated_count = 0
        for origin in origins:
            origin_date = date.fromisoformat(origin.recurrence_origin_date)
            if target <= origin_date or not self._occurs_on(origin, target):
                continue
            key = (origin.series_id, task_date)
            if key in existing_keys:
                continue
            occurrence = Task(
                origin.title,
                task_date,
                origin.start_time,
                origin.end_time,
                repeat_rule=origin.repeat_rule,
                series_id=origin.series_id,
                recurrence_origin_date=origin.recurrence_origin_date,
                repeat_weekday=origin.repeat_weekday,
                repeat_monthday=origin.repeat_monthday,
                recurrence_start_date=origin.recurrence_start_date,
                recurrence_end_date=origin.recurrence_end_date,
                generated=True,
            )
            self.tasks.append(occurrence)
            existing_keys.add(key)
            generated_count += 1
        return generated_count

    @staticmethod
    def _occurs_on(origin, target):
        origin_date = date.fromisoformat(origin.recurrence_origin_date)
        start_date = date.fromisoformat(
            origin.recurrence_start_date or origin.recurrence_origin_date
        )
        end_date = (
            date.fromisoformat(origin.recurrence_end_date)
            if origin.recurrence_end_date
            else None
        )
        if target < start_date or (end_date is not None and target > end_date):
            return False
        days = (target - origin_date).days
        if days < 0:
            return False
        if origin.repeat_rule == "daily":
            return True
        if origin.repeat_rule == "weekly":
            return target.weekday() == origin.repeat_weekday
        if origin.repeat_rule == "monthly":
            month_distance = (
                (target.year - origin_date.year) * 12
                + target.month
                - origin_date.month
            )
            if month_distance < 0:
                return False
            last_day = calendar.monthrange(target.year, target.month)[1]
            return target.day == min(origin.repeat_monthday, last_day)
        return False

    def find_task(self, task_id):
        """按稳定 ID 查找任务。"""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise ValueError("没有找到这条任务")

    def update_task(
        self,
        task_id,
        title,
        task_date,
        start_time=None,
        end_time=None,
        repeat_rule="none",
        repeat_weekday=None,
        repeat_monthday=None,
        recurrence_start_date=None,
        recurrence_end_date=None,
    ):
        """完整校验后再更新，失败时保留原任务。"""
        target = self.find_task(task_id)
        checked_date = validate_new_task_date(task_date)
        checked_start, checked_end = validate_time_range(start_time, end_time)
        checked_repeat = validate_repeat_rule(repeat_rule)

        # 系列自动生成项只编辑本次内容，不改变整个系列的起点与范围。
        if target.generated:
            checked_title = Task(
                title,
                checked_date,
                checked_start,
                checked_end,
                repeat_rule=target.repeat_rule,
                series_id=target.series_id,
                recurrence_origin_date=target.recurrence_origin_date,
                repeat_weekday=target.repeat_weekday,
                repeat_monthday=target.repeat_monthday,
                recurrence_start_date=target.recurrence_start_date,
                recurrence_end_date=target.recurrence_end_date,
                generated=True,
            )
            target.set_title(checked_title.title)
            target.task_date = checked_date
            target.start_time = checked_start
            target.end_time = checked_end
            return target

        recurrence_start_date, recurrence_end_date = self._validate_repeat_range(
            checked_date,
            checked_repeat,
            recurrence_start_date,
            recurrence_end_date,
        )
        effective_date = self._first_occurrence(
            recurrence_start_date or checked_date,
            checked_repeat,
            repeat_weekday,
            repeat_monthday,
        )

        # 用临时 Task 验证标题和重复日期，所有检查成功后才修改 target。
        checked_task = Task(
            title,
            effective_date,
            checked_start,
            checked_end,
            repeat_rule=checked_repeat,
            recurrence_origin_date=effective_date,
            repeat_weekday=repeat_weekday,
            repeat_monthday=repeat_monthday,
            recurrence_start_date=recurrence_start_date,
            recurrence_end_date=recurrence_end_date,
        )
        target.set_title(checked_task.title)
        target.task_date = effective_date
        target.start_time = checked_start
        target.end_time = checked_end
        target.repeat_rule = checked_repeat
        target.repeat_weekday = checked_task.repeat_weekday
        target.repeat_monthday = checked_task.repeat_monthday
        target.recurrence_start_date = checked_task.recurrence_start_date
        target.recurrence_end_date = checked_task.recurrence_end_date
        if not target.generated:
            target.recurrence_origin_date = effective_date
        return target

    @staticmethod
    def _validate_repeat_range(
        task_date,
        repeat_rule,
        recurrence_start_date=None,
        recurrence_end_date=None,
    ):
        """重复区间可独立省略；当前 1.1 只对每日任务开放。"""
        if repeat_rule != "daily":
            if recurrence_start_date is not None or recurrence_end_date is not None:
                raise ValueError("重复起止日期目前只用于每日任务")
            return None, None

        checked_start = (
            validate_new_task_date(recurrence_start_date)
            if recurrence_start_date
            else None
        )
        checked_end = (
            validate_new_task_date(recurrence_end_date)
            if recurrence_end_date
            else None
        )
        effective_start = checked_start or task_date
        if checked_end and checked_end < effective_start:
            raise ValueError("重复结束日期不能早于开始日期")
        return checked_start, checked_end

    @staticmethod
    def _first_occurrence(
        task_date,
        repeat_rule,
        repeat_weekday=None,
        repeat_monthday=None,
    ):
        """让每周/每月任务从用户选定的星期或日期首次出现。"""
        base = date.fromisoformat(task_date)
        if repeat_rule == "weekly" and repeat_weekday is not None:
            return (base + timedelta(days=(repeat_weekday - base.weekday()) % 7)).isoformat()
        if repeat_rule == "monthly" and repeat_monthday is not None:
            last_day = calendar.monthrange(base.year, base.month)[1]
            candidate = base.replace(day=min(repeat_monthday, last_day))
            if candidate < base:
                year = base.year + (1 if base.month == 12 else 0)
                month = 1 if base.month == 12 else base.month + 1
                last_day = calendar.monthrange(year, month)[1]
                candidate = date(year, month, min(repeat_monthday, last_day))
            return candidate.isoformat()
        return task_date

    def delete_task(self, task_id):
        """删除并返回指定任务。"""
        target = self.find_task(task_id)
        if date.fromisoformat(target.task_date) < date.today():
            raise ValueError("历史任务只能查看，不能删除")
        # 单独删除一次重复任务时保留隐藏标记，避免下次查看又自动生成。
        if target.generated:
            target.cancelled = True
        else:
            self.tasks.remove(target)
        return target

    def delete_recurring(self, task_id, scope):
        """按范围删除整个重复系列，或删除所选日期及以后的任务。"""
        target = self.find_task(task_id)
        if target.repeat_rule == "none":
            return self.delete_task(task_id)
        if scope not in ("all", "future"):
            raise ValueError("删除范围必须是 all 或 future")
        cutoff = date.fromisoformat(target.task_date)
        if cutoff < date.today():
            raise ValueError("历史任务只能查看，不能删除")

        series = [task for task in self.tasks if task.series_id == target.series_id]
        if scope == "all":
            self.tasks = [
                task for task in self.tasks if task.series_id != target.series_id
            ]
            return series

        origin = next((task for task in series if not task.generated), None)
        if origin is not None and date.fromisoformat(origin.task_date) < cutoff:
            origin.recurrence_end_date = (cutoff - timedelta(days=1)).isoformat()
        self.tasks = [
            task
            for task in self.tasks
            if not (
                task.series_id == target.series_id
                and date.fromisoformat(task.task_date) >= cutoff
            )
        ]
        return series

    def toggle_task(self, task_id, allow_early_completion=True):
        """切换任务完成状态；历史任务保持只读。"""
        target = self.find_task(task_id)
        if date.fromisoformat(target.task_date) < date.today():
            raise ValueError("历史任务只能查看，不能修改")
        if (
            not allow_early_completion
            and date.fromisoformat(target.task_date) > date.today()
        ):
            raise ValueError("设置中已禁止提前完成未来任务")
        target.toggle_completed()
        return target

    def completion_for_date(self, task_date):
        """返回 (完成数, 总数, 整数百分比)。"""
        # 【助手接入】正式使用周子编写的日期统计函数。
        summary = calculate_daily_summary(self.tasks, task_date)
        return summary["completed"], summary["total"], summary["percentage"]
