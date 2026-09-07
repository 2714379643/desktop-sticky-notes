"""单条待办任务的数据模型。"""

from uuid import uuid4


class Task:
    """保存一条任务的内容、日期、可选时间和完成状态。"""

    def __init__(
        self,
        title,
        task_date,
        start_time=None,
        end_time=None,
        task_id=None,
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
        self.completed = False

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
        }

    @classmethod
    def from_dict(cls, data):
        # 【助手编写，周子参与前置尝试】把保存的字典恢复成 Task。
        if not isinstance(data, dict):
            raise TypeError("任务数据必须是字典")
        if not isinstance(data["completed"], bool):
            raise TypeError("完成状态必须是布尔值")

        task = cls(
            title=data["title"],
            task_date=data["task_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            # 兼容早期没有 ID 的数据，首次自动保存后会补上 ID。
            task_id=data.get("task_id"),
        )
        task.completed = data["completed"]
        return task
