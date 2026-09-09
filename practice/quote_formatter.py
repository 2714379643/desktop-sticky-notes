"""周子的语录整理练习：已审查并接入正式代码。"""

from sticky_notes.quote_formatter import normalize_quote


if __name__ == "__main__":
    sample = "  Keep going.  \n  继续前进。 \n ——周子  "
    expected = "Keep going.\n继续前进。\n——周子"
    assert normalize_quote(sample) == expected
    print("练习 1 测试通过，代码已接入 sticky_notes/quote_formatter.py")
