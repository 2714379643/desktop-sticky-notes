"""月历日期网格的纯 Python 计算。"""

import calendar
from datetime import date, timedelta


def build_month_rows(year, month):
    """返回按周排列的日期；当前月结束后最多保留一行下月日期。"""
    if isinstance(year, bool) or not isinstance(year, int):
        raise TypeError("year 必须是整数")
    if isinstance(month, bool) or not isinstance(month, int):
        raise TypeError("month 必须是整数")
    date(year, month, 1)  # 交给 date 校验年份和月份范围。

    rows = calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(
        year,
        month,
    )

    # 如果当月正好在星期日结束，补一行下月日期，便于直接切换。
    if all(day.month == month for day in rows[-1]):
        first_next_day = rows[-1][-1] + timedelta(days=1)
        rows.append(
            [first_next_day + timedelta(days=offset) for offset in range(7)]
        )

    return rows


def normalize_calendar_date(value):
    """把自定义月历的 date 或 Qt 的 QDate 统一成 Python date。"""
    if isinstance(value, date):
        return value

    converter = getattr(value, "toPython", None)
    if callable(converter):
        converted = converter()
        if isinstance(converted, date):
            return converted

    raise TypeError("日期必须是 date 或可转换的 Qt 日期对象")
