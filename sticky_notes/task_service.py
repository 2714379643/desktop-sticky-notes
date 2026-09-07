"""任务业务管理：创建、查询、编辑、删除和切换完成状态。"""

from datetime import date

from sticky_notes.models.task import Task
from sticky_notes.task_statistics import calculate_daily_summary
from sticky_notes.validators import validate_new_task_date, validate_time_range


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

    def add_task(self, title, task_date, start_time=None, end_time=None):
        """校验并添加任务，返回新建的 Task 对象。"""
        # 【周子编写，审查后修正】核心流程：校验、构造、追加并返回。
        task_date = validate_new_task_date(task_date)
        start_time, end_time = validate_time_range(start_time, end_time)
        task = Task(title, task_date, start_time, end_time)
        self.tasks.append(task)
        return task

    def get_tasks_by_date(self, task_date):
        """返回指定日期的任务副列表，允许查询过去日期。"""
        # 【周子编写】遍历全部任务并筛选同一天的对象。
        query_result = []
        for task in self.tasks:
            if task.task_date == task_date:
                query_result.append(task)

        # 【助手补充】有时间的任务优先，并按开始时间排序；排序稳定。
        return sorted(
            query_result,
            key=lambda task: (task.start_time is None, task.start_time or ""),
        )

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
    ):
        """完整校验后再更新，失败时保留原任务。"""
        target = self.find_task(task_id)
        checked_date = validate_new_task_date(task_date)
        checked_start, checked_end = validate_time_range(start_time, end_time)

        # 用临时 Task 验证标题，所有检查成功后才修改 target。
        checked_title = Task(title, checked_date, checked_start, checked_end).title
        target.set_title(checked_title)
        target.task_date = checked_date
        target.start_time = checked_start
        target.end_time = checked_end
        return target

    def delete_task(self, task_id):
        """删除并返回指定任务。"""
        target = self.find_task(task_id)
        if date.fromisoformat(target.task_date) < date.today():
            raise ValueError("历史任务只能查看，不能删除")
        self.tasks.remove(target)
        return target

    def toggle_task(self, task_id):
        """切换任务完成状态；历史任务保持只读。"""
        target = self.find_task(task_id)
        if date.fromisoformat(target.task_date) < date.today():
            raise ValueError("历史任务只能查看，不能修改")
        target.toggle_completed()
        return target

    def completion_for_date(self, task_date):
        """返回 (完成数, 总数, 整数百分比)。"""
        # 【助手接入】正式使用周子编写的日期统计函数。
        summary = calculate_daily_summary(self.tasks, task_date)
        return summary["completed"], summary["total"], summary["percentage"]
