"""按日期统计任务完成情况。"""


def calculate_daily_summary(tasks, task_date):
    """返回指定日期的 total、completed、unfinished 和 percentage。"""
    # 【周子编写，审查通过】筛选指定日期并统计完成情况。
    equal_list = []
    completed = 0
    for task in tasks:
        # 【助手补充】被删除的单次重复任务保留隐藏标记，统计时不计入。
        if task.task_date == task_date and not getattr(task, "cancelled", False):
            equal_list.append(task)
            if task.completed:
                completed += 1

    total = len(equal_list)
    unfinished = total - completed
    if total == 0:
        percentage = 0
    else:
        percentage = round(completed / total * 100)

    return {
        "total": total,
        "completed": completed,
        "unfinished": unfinished,
        "percentage": percentage,
    }
