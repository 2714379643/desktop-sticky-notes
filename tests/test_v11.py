"""1.1 新增的重复任务、便携存储与导入导出测试。"""

import calendar
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from sticky_notes.data_exchange import (
    build_import_report,
    export_csv,
    export_json,
    export_txt,
    import_json,
    import_txt,
)
from sticky_notes.calendar_utils import build_month_rows, normalize_calendar_date
from sticky_notes.models.task import Task
from sticky_notes.quote_formatter import normalize_quote
from sticky_notes.quotes.content import QUOTES, load_quotes
from sticky_notes.quotes.daily_quote import get_daily_quote
from sticky_notes.storage import SCHEMA_VERSION, TaskStorage
from sticky_notes.task_service import TaskService
from sticky_notes.themes import THEMES


class CalendarLayoutTests(unittest.TestCase):
    def test_month_rows_only_keep_one_trailing_month_row(self):
        rows = build_month_rows(2026, 9)
        trailing_rows = [
            week for week in rows if any(day.month == 10 for day in week)
        ]
        self.assertEqual(len(trailing_rows), 1)
        self.assertEqual([day.day for day in rows[-1][-4:]], [1, 2, 3, 4])

    def test_month_ending_on_sunday_gets_one_next_month_row(self):
        rows = build_month_rows(2026, 5)
        self.assertTrue(all(day.month == 6 for day in rows[-1]))

    def test_calendar_arguments_reject_boolean_values(self):
        with self.assertRaises(TypeError):
            build_month_rows(True, 9)

    def test_python_date_from_compact_calendar_needs_no_conversion(self):
        selected = date(2026, 9, 8)
        self.assertIs(normalize_calendar_date(selected), selected)

    def test_qt_style_date_is_converted_when_needed(self):
        class FakeQtDate:
            @staticmethod
            def toPython():
                return date(2026, 9, 9)

        self.assertEqual(normalize_calendar_date(FakeQtDate()), date(2026, 9, 9))


class ThemeTests(unittest.TestCase):
    def test_only_mist_theme_uses_translucent_glass(self):
        self.assertEqual(len(THEMES), 8)
        self.assertEqual(THEMES["雾光玻璃"]["mode"], "glass")
        self.assertLess(THEMES["雾光玻璃"]["surface"][3], 160)
        for theme_name, colors in THEMES.items():
            if theme_name == "雾光玻璃":
                continue
            with self.subTest(theme=theme_name):
                self.assertEqual(colors["mode"], "solid")
                self.assertEqual(colors["surface"][3], 255)
                self.assertEqual(len(colors["backdrop"]), 4)


class RecurrenceTests(unittest.TestCase):
    def test_daily_optional_range_limits_generation(self):
        today = date.today()
        start = today + timedelta(days=2)
        end = today + timedelta(days=4)
        service = TaskService()
        origin = service.add_task(
            "区间阅读",
            today.isoformat(),
            repeat_rule="daily",
            recurrence_start_date=start.isoformat(),
            recurrence_end_date=end.isoformat(),
        )
        self.assertEqual(origin.task_date, start.isoformat())
        self.assertEqual(service.ensure_recurring_for_date((start + timedelta(days=1)).isoformat()), 1)
        self.assertEqual(service.ensure_recurring_for_date((end + timedelta(days=1)).isoformat()), 0)

    def test_delete_future_keeps_history_and_stops_generation(self):
        today = date.today()
        service = TaskService()
        origin = service.add_task("每日阅读", today.isoformat(), repeat_rule="daily")
        tomorrow = today + timedelta(days=1)
        later = today + timedelta(days=2)
        service.ensure_recurring_for_date(tomorrow.isoformat())
        target = service.get_tasks_by_date(tomorrow.isoformat())[0]
        service.delete_recurring(target.task_id, "future")
        self.assertIn(origin, service.tasks)
        self.assertEqual(service.get_tasks_by_date(tomorrow.isoformat()), [])
        self.assertEqual(service.ensure_recurring_for_date(later.isoformat()), 0)

    def test_delete_all_removes_whole_series(self):
        today = date.today()
        service = TaskService()
        origin = service.add_task("每日阅读", today.isoformat(), repeat_rule="daily")
        service.ensure_recurring_for_date((today + timedelta(days=1)).isoformat())
        service.delete_recurring(origin.task_id, "all")
        self.assertEqual(service.tasks, [])

    def test_future_completion_can_be_disabled(self):
        service = TaskService()
        task = service.add_task("明日任务", (date.today() + timedelta(days=1)).isoformat())
        with self.assertRaisesRegex(ValueError, "禁止提前完成"):
            service.toggle_task(task.task_id, allow_early_completion=False)
        self.assertFalse(task.completed)

    def test_daily_occurrence_is_generated_only_once(self):
        today = date.today()
        target = today + timedelta(days=1)
        service = TaskService()
        origin = service.add_task("每日阅读", today.isoformat(), repeat_rule="daily")

        self.assertEqual(service.ensure_recurring_for_date(target.isoformat()), 1)
        self.assertEqual(service.ensure_recurring_for_date(target.isoformat()), 0)
        tasks = service.get_tasks_by_date(target.isoformat())
        self.assertEqual(len(tasks), 1)
        self.assertTrue(tasks[0].generated)
        self.assertEqual(tasks[0].series_id, origin.series_id)
        self.assertFalse(tasks[0].completed)

    def test_deleted_occurrence_does_not_come_back(self):
        today = date.today()
        target = today + timedelta(days=1)
        service = TaskService()
        service.add_task("每日阅读", today.isoformat(), repeat_rule="daily")
        service.ensure_recurring_for_date(target.isoformat())
        occurrence = service.get_tasks_by_date(target.isoformat())[0]
        service.delete_task(occurrence.task_id)
        self.assertEqual(service.get_tasks_by_date(target.isoformat()), [])
        self.assertEqual(service.ensure_recurring_for_date(target.isoformat()), 0)

    def test_weekly_rule_matches_same_weekday(self):
        origin = Task(
            "周复盘",
            "2026-09-08",
            repeat_rule="weekly",
            recurrence_origin_date="2026-09-08",
        )
        self.assertTrue(TaskService._occurs_on(origin, date(2026, 9, 15)))
        self.assertFalse(TaskService._occurs_on(origin, date(2026, 9, 16)))

    def test_weekly_rule_uses_explicit_selected_weekday(self):
        origin = Task(
            "周五复盘",
            "2026-09-08",
            repeat_rule="weekly",
            recurrence_origin_date="2026-09-08",
            repeat_weekday=4,
        )
        self.assertTrue(TaskService._occurs_on(origin, date(2026, 9, 11)))
        self.assertFalse(TaskService._occurs_on(origin, date(2026, 9, 15)))

    def test_weekly_task_starts_on_selected_weekday(self):
        today = date.today()
        selected_weekday = (today.weekday() + 3) % 7
        service = TaskService()
        task = service.add_task(
            "指定星期任务",
            today.isoformat(),
            repeat_rule="weekly",
            repeat_weekday=selected_weekday,
        )
        self.assertEqual(date.fromisoformat(task.task_date).weekday(), selected_weekday)

    def test_monthly_rule_uses_last_day_for_short_month(self):
        origin = Task(
            "月末整理",
            "2026-01-31",
            repeat_rule="monthly",
            recurrence_origin_date="2026-01-31",
        )
        last_february_day = calendar.monthrange(2026, 2)[1]
        self.assertTrue(
            TaskService._occurs_on(origin, date(2026, 2, last_february_day))
        )
        self.assertTrue(TaskService._occurs_on(origin, date(2026, 3, 31)))

    def test_monthly_rule_uses_explicit_selected_day(self):
        origin = Task(
            "每月十五号整理",
            "2026-01-20",
            repeat_rule="monthly",
            recurrence_origin_date="2026-01-20",
            repeat_monthday=15,
        )
        self.assertTrue(TaskService._occurs_on(origin, date(2026, 2, 15)))
        self.assertFalse(TaskService._occurs_on(origin, date(2026, 2, 20)))

    def test_monthly_task_starts_on_selected_day(self):
        today = date.today()
        service = TaskService()
        task = service.add_task(
            "每月一号",
            today.isoformat(),
            repeat_rule="monthly",
            repeat_monthday=1,
        )
        first = date.fromisoformat(task.task_date)
        self.assertGreaterEqual(first, today)
        self.assertEqual(first.day, 1)


class ExchangeTests(unittest.TestCase):
    def test_legacy_json_without_settings_can_be_merged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "old.json"
            source.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "tasks": [{
                            "title": "最早版本任务",
                            "task_date": "2020-01-01",
                            "start_time": None,
                            "end_time": None,
                            "completed": True,
                        }],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            service = TaskService()
            result = import_json(source, service)
            self.assertEqual(result.imported, 1)
            self.assertEqual(service.tasks[0].title, "最早版本任务")

    def test_import_report_from_student_exercise(self):
        self.assertEqual(
            build_import_report(2, 1, ["第 4 行：日期无效"]),
            "成功导入 2 条，跳过 1 条。\n\n第 4 行：日期无效",
        )
        self.assertEqual(
            build_import_report(0, 0, []),
            "成功导入 0 条，跳过 0 条。",
        )
        with self.assertRaises(ValueError):
            build_import_report(True, 0, [])

    def test_txt_import_reports_bad_rows_and_keeps_good_rows(self):
        today = date.today().isoformat()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tasks.txt"
            source.write_text(
                "date|start_time|end_time|title|repeat\n"
                f"{today}|08:30|09:30|学习 Python|daily\n"
                f"{today}|10:00||缺少结束时间|none\n",
                encoding="utf-8",
            )
            service = TaskService()
            result = import_txt(source, service)
            self.assertEqual(result.imported, 1)
            self.assertEqual(result.skipped, 1)
            self.assertEqual(service.tasks[0].repeat_rule, "daily")

    def test_txt_import_keeps_selected_weekday_and_month_day(self):
        today = date.today().isoformat()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tasks.txt"
            source.write_text(
                "date|start_time|end_time|title|repeat|weekday|month_day\n"
                f"{today}|||周五复盘|weekly|5|\n"
                f"{today}|||月末整理|monthly||31\n",
                encoding="utf-8",
            )
            service = TaskService()
            result = import_txt(source, service)
            self.assertEqual(result.imported, 2)
            self.assertEqual(service.tasks[0].repeat_weekday, 4)
            self.assertEqual(service.tasks[1].repeat_monthday, 31)

    def test_all_export_formats_are_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = [Task("备份测试", date.today().isoformat())]
            export_json(root / "tasks.json", tasks, {"theme": "雾光玻璃"})
            export_txt(root / "tasks.txt", tasks)
            export_csv(root / "tasks.csv", tasks)
            self.assertIn("备份测试", (root / "tasks.json").read_text("utf-8"))
            self.assertIn("date|start_time", (root / "tasks.txt").read_text("utf-8-sig"))
            self.assertIn("task_id,date", (root / "tasks.csv").read_text("utf-8-sig"))


class SchemaTests(unittest.TestCase):
    def test_v1_file_loads_and_next_save_becomes_current_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "tasks": [
                            {
                                "title": "旧任务",
                                "task_date": "2026-09-08",
                                "start_time": None,
                                "end_time": None,
                                "completed": False,
                            }
                        ],
                        "settings": {"theme": "奶油纸"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            storage = TaskStorage(path)
            tasks, settings, _ = storage.load()
            self.assertEqual(tasks[0].repeat_rule, "none")
            self.assertEqual(settings["theme"], "日式庭院纸")
            storage.save(tasks, settings)
            payload = json.loads(path.read_text("utf-8"))
            self.assertEqual(payload["schema_version"], SCHEMA_VERSION)

    def test_v2_repeat_task_infers_missing_repeat_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "tasks": [
                            {
                                "task_id": "old-weekly-task",
                                "title": "旧版周任务",
                                "task_date": "2026-09-08",
                                "start_time": None,
                                "end_time": None,
                                "completed": False,
                                "repeat_rule": "weekly",
                                "series_id": "old-weekly-task",
                                "recurrence_origin_date": "2026-09-08",
                                "generated": False,
                                "cancelled": False,
                            }
                        ],
                        "settings": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            tasks, _, _ = TaskStorage(path).load()
            self.assertEqual(tasks[0].repeat_weekday, date(2026, 9, 8).weekday())


class QuoteFormatterTests(unittest.TestCase):
    def test_student_quote_formatter_preserves_middle_blank_line(self):
        source = " \n  Keep going.  \n\n 继续前进。 \n "
        self.assertEqual(normalize_quote(source), "Keep going.\n\n继续前进。")

    def test_student_quote_formatter_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            normalize_quote(" \n\t ")


class DailyQuoteTests(unittest.TestCase):
    def test_quote_file_contains_all_unique_blocks(self):
        self.assertEqual(len(QUOTES), 101)
        self.assertEqual(len(QUOTES), len(set(QUOTES)))
        self.assertIn(
            "If Winter comes, can Spring be far behind?\n"
            "冬天来了，春天还会远吗？\n"
            "——雪莱，《西风颂》",
            QUOTES,
        )

    def test_external_quote_file_supports_mixed_block_lengths(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quotes.txt"
            path.write_text(
                "单段文案\n\n"
                "English quote.\n"
                "中文翻译\n\n"
                "Another quote.\n"
                "另一条翻译\n"
                "——作者\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_quotes(path),
                [
                    "单段文案",
                    "English quote.\n中文翻译",
                    "Another quote.\n另一条翻译\n——作者",
                ],
            )

    def test_quote_blocks_must_be_separated_by_blank_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quotes.txt"
            path.write_text("第一行\n第二行\n第三行\n第四行", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "保留一个空行"):
                load_quotes(path)

    def test_same_date_always_returns_same_quote(self):
        selected = date(2026, 9, 8)
        self.assertEqual(get_daily_quote(selected), get_daily_quote(selected))

    def test_every_30_day_window_has_no_duplicates(self):
        first_day = date(2026, 1, 1)
        self.assertGreaterEqual(len(set(QUOTES)), 30)
        for offset in range(60):
            results = [
                get_daily_quote(first_day + timedelta(days=offset + number))
                for number in range(30)
            ]
            self.assertEqual(len(results), len(set(results)))

    def test_invalid_date_type_is_rejected(self):
        for value in (0, "", False):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    get_daily_quote(value)


if __name__ == "__main__":
    unittest.main()
