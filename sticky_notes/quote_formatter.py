"""励志语录文本整理。"""


def normalize_quote(text):
    """去掉每行首尾空格和首尾空行，同时保留中间的换行。"""
    # 【周子编写，助手指导，审查通过】
    if not isinstance(text, str):
        raise TypeError("语录必须是字符串")

    lines = text.splitlines()
    for index in range(len(lines)):
        lines[index] = lines[index].strip()

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    result = "\n".join(lines)
    if result == "":
        raise ValueError("语录不能为空")
    return result
