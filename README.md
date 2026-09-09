# Desktop Sticky Notes 1.1

一个完全使用 Python 与 PySide6 编写的 Windows 桌面待办便签。

## 1.1 新功能

- 只有“雾光玻璃”使用可透出桌面背景的原生亚克力材质，并使用三层高光轮廓、低亮度底色和更清晰的玻璃进度条；其余七套主题保持不透明材质。
- 七套装饰主题分别还原概念图中的松枝落花与朱印、马卡龙云层与晨日、水墨竹叶与远山、黑金星座与月相、瑞士红色构成、森林蕨叶与浆果，以及“伊蕾娜旅记”的人物、星图与月牙。
- 主窗口改为单层柔和圆角轮廓，去掉较重的双层外框。
- 任务使用连续横向列表和细分隔线，不再使用大块卡片。
- 八套主题统一采用 D 版添加位置：立体圆形加号固定在进度条右侧，并随主题变换材质和强调色。
- 设置按钮改为自绘滑杆图标，不依赖系统字体里的齿轮符号；主题下拉列表使用独立前景色与背景色，深色主题也不会隐藏文字。
- 窗口右下角可拖动缩放，始终保持约 `490:710` 的长宽比例；字体和间距会跟随缩放。
- 底部日期可点击打开紧凑单月月历，也可以用左右按钮逐日切换；默认查看今天。日期格只显示一行公历数字，当月结束后最多显示一行下月日期。仅在当日有任务且全部完成时显示红点。
- 励志文案移到底部，从 `quotes` 包读取；短句自动放大，所有文案上下左右居中，最小字号仍放不下时才在框内滚动。
- 手动录入弹窗按概念图改为无系统标题栏的圆角主题面板，完整月历直接嵌入顶部；时间使用小时与分钟滚轮。
- 支持每天、每周、每月重复任务；每周可选择星期几，每月可选择 1—31 号。每日任务可分别选择或留空开始、结束日期。
- 删除重复任务时，可选择删除整个系列，或删除所选日期及以后的任务。
- 设置中可禁止提前勾选未来任务；仍可提前添加和编辑任务。
- 支持新版 TXT、旧版 5/7 字段 TXT 和 1.0 版 JSON 导入，并可导出 JSON、TXT 或 CSV。
- 关闭窗口时可缩到系统托盘；点击托盘图标重新打开，右键选择“退出并保存”。
- 自动保存不再刷新任务列表，也不改变状态文字，因此保存时页面保持静止。
- 源码运行时在项目旁创建 `msgs`；打包后在 EXE 旁创建 `msgs`，不再固定 D 盘路径。
- 兼容旧版数据文件；下次保存时自动升级为 v4 格式。

## 运行源码

### 2026-09-09 控件修正

- 设置、关闭、日期前后切换、字号加减使用统一正圆控件，固定宽高并同步 QSS 尺寸，防止主题样式挤压变形。
- 设置选项的复选标记改为圆形，仍然可以分别独立勾选。
- 主题选择框右侧显示圆形箭头，菜单文字随主题保持可见。
- 设置窗口收窄为 420 个逻辑像素，紧凑单列排版，不包含滚动区域。导入的详细说明改为点击“查看导入模板”打开。
- 改动不调整数据格式，不清空任务或原有设置。

新增 6 项可选 Qt UI 测试。在 Windows CMD 中运行：

```bat
set STICKY_UI_TESTS=1
python -m unittest discover -s tests -v
set STICKY_UI_TESTS=
```

包含原有逻辑测试共 49 项；未启用 UI 测试时保留原有 43 项测试并跳过 6 项 Qt 实测。

建议使用 Python 3.11 或更高版本。在项目根目录执行：

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

PyCharm 中也可以直接运行根目录的 `main.py`。

## 生成 Windows EXE

先从右下角托盘彻底退出正在运行的旧版程序，再双击项目根目录的：

```text
build_exe.bat
```

完成后生成：

```text
dist\DesktopStickyNotes.exe
dist\励志语录100条.txt
```

EXE 会优先读取旁边的 `励志语录100条.txt`，因此修改文案后重新启动程序即可生效，不需要重新打包。如果这个外部文件被删除，程序会读取打包在 EXE 内的备用副本。

第一次运行 EXE 后，数据位于：

```text
dist\msgs\data.json
```

如果把 EXE 移到其他文件夹，新的 `msgs` 也会在那个 EXE 旁创建。因此发布给别人时，可以把 EXE 和它旁边的 `msgs` 文件夹一起复制；只复制 EXE 相当于使用全新数据。

若项目根目录原来已有 `msgs\data.json`，新版 EXE 第一次启动时会尝试复制旧数据到新位置，不会删除原文件。

## TXT 导入模板

项目中提供了 `docs\TXT导入模板.txt`。要求：

- 文件编码为 UTF-8。
- 每行一项任务，字段顺序固定。
- 字段之间使用英文竖线 `|`。
- 日期必须是今天或未来，格式为 `YYYY-MM-DD`。
- 时间要么都不填，要么同时填写，格式为 `HH:MM`。
- 重复规则只能是 `none`、`daily`、`weekly`、`monthly`。
- 每周任务在 `weekday` 填 `1` 到 `7`，依次代表星期一到星期日。
- 每月任务在 `month_day` 填 `1` 到 `31`；短月份会自动使用最后一天。
- 每日任务可在 `repeat_start` 和 `repeat_end` 填可选日期，两项可以分别留空。

```text
date|start_time|end_time|title|repeat|weekday|month_day|repeat_start|repeat_end
2099-09-08|08:30|10:00|学习 Python|none||||
2099-09-09|||每日阅读|daily|||2099-09-12|2099-10-12
```

TXT 导入遇到错误行时会跳过该行，继续导入其他正确任务，最后给出汇总。

## 每日文案显示规则

设置页不再提供文案输入框。源码运行时，`content.py` 会直接读取同级目录中的 `sticky_notes\quotes\励志语录100条.txt`；打包后则优先读取 EXE 旁边的同名文件。不同文案之间保留一个空行，每条文案内部可以直接写一至三行，不需要序号或缩进。显示框会从大字号开始自动测量：能完整显示就保持较大字号，空间不够则逐级缩小；所有文案都上下左右居中，达到最小字号仍放不下时才出现纵向滚动条。

`sticky_notes\quotes\daily_quote.py` 负责按日期选择文案。周子编写的算法先使用固定种子打乱全部文案，再通过日期序号选择当天内容，因此关闭、重开程序后仍显示同一句，并保证现有文案在 30 天内不重复。

## 重复任务规则

- 每天：从任务日期开始，每天出现。
- 每周：由用户选择星期一至星期日；旧数据会按原任务日期的星期自动补全。
- 每月：由用户选择 1—31 号；如果月份较短，使用当月最后一天。例如选择 31 号，会在 2 月最后一天和 3 月 31 日出现。
- 每次生成的任务拥有独立完成状态。

## 项目结构

```text
desktop-sticky-notes-v1.1/
├─ main.py
├─ build_exe.bat
├─ requirements.txt
├─ docs/
│  └─ TXT导入模板.txt
├─ sticky_notes/
│  ├─ controller.py
│  ├─ data_exchange.py
│  ├─ desktop_windows.py
│  ├─ icons.py
│  ├─ calendar_utils.py
│  ├─ quote_formatter.py
│  ├─ quotes/
│  │  ├─ __init__.py
│  │  ├─ content.py
│  │  ├─ daily_quote.py
│  │  └─ 励志语录100条.txt
│  ├─ assets/
│  │  └─ elaina_vignette.png
│  ├─ storage.py
│  ├─ task_service.py
│  ├─ task_statistics.py
│  ├─ themes.py
│  ├─ validators.py
│  ├─ models/task.py
│  └─ ui/
│     ├─ month_calendar.py
│     ├─ date_picker.py
│     ├─ note_window.py
│     ├─ settings_dialog.py
│     └─ task_dialog.py
├─ practice/
│  ├─ quote_formatter.py
│  └─ import_report.py
└─ tests/
   ├─ test_core.py
   └─ test_v11.py
```

## 测试

```bat
python -m unittest discover -s tests -v
```

当前 43 项自动测试包括任务增删改查、时间校验、旧数据恢复、重复区间和删除范围、旧版 JSON/TXT 导入、三种导出格式、月历日期转换以及主题材质配置。

## 周子的代码贡献

三份练习都已完成审查并接入正式功能：

- `normalize_quote()`：正式代码位于 `sticky_notes\quote_formatter.py`，负责整理多行语录。
- `build_import_report()`：正式代码位于 `sticky_notes\data_exchange.py`，负责生成导入结果文字。
- `get_daily_quote()`：正式代码位于 `sticky_notes\quotes\daily_quote.py`，负责稳定选择当天文案并避免 30 天内重复。

可以通过原练习入口复测：

```bat
python -m practice.quote_formatter
python -m practice.import_report
python -m sticky_notes.quotes.daily_quote
```

正式源码保留了 `【周子编写，助手指导，审查通过】` 注释。

`daily_quote.py` 已通过审查并接入主窗口。

## Git 提交建议

先不要覆盖已经发布的 1.0。确认 1.1 在你的 Windows 电脑上运行正常后，在项目根目录执行：

```bat
git checkout -b v1.1-dev
git add .
git commit -m "feat: 开发桌面便签 1.1"
```

练习代码审查和合并完成后，再决定是否合并到 `main`。
