"""周子已完成的任务统计练习。

正式实现已接入 sticky_notes/task_statistics.py。
仍可从项目根目录运行：python -m practice.task_statistics
"""

from datetime import date

from sticky_notes.models.task import Task
from sticky_notes.task_statistics import calculate_daily_summary


if __name__ == "__main__":
    today = date.today().isoformat()
    first = Task("复习 Python", today)
    second = Task("整理项目", today)
    first.toggle_completed()

    result = calculate_daily_summary([first, second], today)
    expected = {
        "total": 2,
        "completed": 1,
        "unfinished": 1,
        "percentage": 50,
    }
    print("你的结果：", result)
    print("预期结果：", expected)
    assert result == expected, "结果还不正确，请按注释继续检查"
    print("练习通过！")
