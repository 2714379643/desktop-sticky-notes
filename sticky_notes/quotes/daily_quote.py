"""按日期稳定选择文案，并确保 30 天内不重复。"""

from datetime import date
from random import Random

from sticky_notes.quotes.content import QUOTES


def get_daily_quote(current_date=None):
    """返回指定日期的文案；同一天稳定，完整循环前不会重复。"""
    # 【周子编写，助手指导，审查通过】
    if current_date is None:
        current_date = date.today()
    if not isinstance(current_date, date):
        raise TypeError("日期必须是 date 对象")
    quote_pool = QUOTES.copy()

    # 固定种子保证每次启动得到相同的打乱顺序。
    random_generator = Random("desktop-sticky-notes-v1.1")
    random_generator.shuffle(quote_pool)

    # 日期序号每天增加 1；走完全部文案后才会进入下一轮。
    day_index = current_date.toordinal() % len(quote_pool)
    return quote_pool[day_index]


if __name__ == "__main__":
    from datetime import timedelta

    start_date = date(2026, 9, 8)
    results = []

    for number in range(30):
        current = start_date + timedelta(days=number)
        results.append(get_daily_quote(current))

    assert len(results) == len(set(results))
    print("30 天文案无重复，测试通过")
