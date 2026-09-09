"""周子的导入报告练习：已审查并接入正式代码。"""

from sticky_notes.data_exchange import build_import_report


if __name__ == "__main__":
    result = build_import_report(2, 1, ["第 4 行：日期无效"])
    assert result == "成功导入 2 条，跳过 1 条。\n\n第 4 行：日期无效"
    print("练习 2 测试通过，代码已接入 sticky_notes/data_exchange.py")
