"""核心逻辑自动测试，全部使用临时数据。"""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from sticky_notes.models.task import Task
from sticky_notes.storage import StorageError, TaskStorage
from sticky_notes.task_service import TaskService
from sticky_notes.task_statistics import calculate_daily_summary
from sticky_notes.validators import validate_time_range


class TaskTests(unittest.TestCase):
    def test_round_trip_keeps_id_and_state(self):
        task = Task("复习 Python", "2026-09-07", "09:00", "10:00")
        task.toggle_completed()
        restored = Task.from_dict(task.to_dict())
        self.assertEqual(restored.to_dict(), task.to_dict())
        self.assertIsNot(restored, task)

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            Task("   ", "2026-09-07")


class ValidatorTests(unittest.TestCase):
    def test_empty_times_are_allowed(self):
        self.assertEqual(validate_time_range(), (None, None))

    def test_one_time_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_time_range("09:00", "")

    def test_reverse_time_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_time_range("10:00", "09:00")


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.today = date.today().isoformat()
        self.tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.service = TaskService()

    def test_add_query_toggle_update_delete(self):
        task = self.service.add_task("学习 Git", self.today, "09:00", "10:00")
        self.assertEqual(self.service.get_tasks_by_date(self.today), [task])
        self.service.toggle_task(task.task_id)
        self.assertTrue(task.completed)
        self.service.update_task(task.task_id, "学习 GitHub", self.tomorrow)
        self.assertEqual(task.title, "学习 GitHub")
        self.assertEqual(self.service.get_tasks_by_date(self.today), [])
        self.assertEqual(self.service.get_tasks_by_date(self.tomorrow), [task])
        self.assertIs(self.service.delete_task(task.task_id), task)
        self.assertEqual(self.service.tasks, [])

    def test_daily_summary_uses_only_selected_date(self):
        first = self.service.add_task("第一项", self.today)
        self.service.add_task("第二项", self.today)
        self.service.add_task("明天的任务", self.tomorrow).toggle_completed()
        first.toggle_completed()

        self.assertEqual(
            calculate_daily_summary(self.service.tasks, self.today),
            {
                "total": 2,
                "completed": 1,
                "unfinished": 1,
                "percentage": 50,
            },
        )

    def test_invalid_add_does_not_leave_half_task(self):
        with self.assertRaises(ValueError):
            self.service.add_task("错误时间", self.today, "12:00", "11:00")
        self.assertEqual(self.service.tasks, [])


class StorageTests(unittest.TestCase):
    def test_save_load_and_backup_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "data.json"
            storage = TaskStorage(data_path)
            first = Task("第一项", "2020-01-01")
            storage.save([first], {"theme": "奶油纸"})
            storage.save([first, Task("第二项", "2020-01-02")], {"theme": "鼠尾草"})

            tasks, settings, recovered = storage.load()
            self.assertFalse(recovered)
            self.assertEqual(len(tasks), 2)
            # v1.1 会把旧主题名迁移为新的玻璃主题。
            self.assertEqual(settings["theme"], "雾光玻璃")
            self.assertEqual(tasks[0].task_id, first.task_id)

            data_path.write_text("{broken", encoding="utf-8")
            tasks, settings, recovered = storage.load()
            self.assertTrue(recovered)
            self.assertEqual([task.title for task in tasks], ["第一项"])

    def test_invalid_completed_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "data.json"
            payload = {
                "schema_version": 1,
                "tasks": [{
                    "title": "错误数据",
                    "task_date": "2026-09-07",
                    "start_time": None,
                    "end_time": None,
                    "completed": "False",
                }],
                "settings": {},
            }
            data_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(StorageError):
                TaskStorage(data_path).load()


if __name__ == "__main__":
    unittest.main()
