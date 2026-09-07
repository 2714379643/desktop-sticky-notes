# Desktop Sticky Notes

一个完全使用 Python 与 PySide6 编写的 Windows 桌面待办便签。

## 已实现

- 默认查看今天，月历可切换过去或未来日期，也可跨月、跨年。
- 过去任务只读；新增和编辑日期不能早于今天。
- 任务时间可以全部不填；若填写，开始和结束时间必须同时存在。
- 勾选后显示删除线，可取消完成；支持编辑和删除今天、未来的任务。
- 标题显示 `YYYY.M.D To do list`，并显示完成数量与进度。
- 奶油纸、鼠尾草、浅玫瑰三种主题和 12～22 px 字号。
- 任务、主题、字号和窗口位置自动保存；保存时保留有效备份。
- 默认位于普通应用下方、桌面壁纸上方；设置中可以关闭。
- 同一时间只允许运行一个实例，避免两个窗口覆盖数据。

图钉与纸张由 Qt 绘制，没有需要联网加载或版权不明的图片。

## 运行

建议使用 Python 3.11 或更高版本。在项目根目录执行：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

PyCharm 中也可以直接运行根目录的 `main.py`。

## 生成可直接运行的 Windows EXE

在 Windows 上双击项目根目录的：

```text
build_exe.bat
```

脚本会自动创建或复用 `.venv`，安装打包依赖并生成：

```text
dist\DesktopStickyNotes.exe
```

这个 EXE 是单文件窗口程序，运行时不会出现黑色控制台窗口。复制到另一台 64 位 Windows 电脑后可以直接运行，不要求对方安装 Python。单文件程序首次启动时需要先释放内部文件，因此可能比源码启动稍慢。

PyInstaller 生成物与构建系统有关，因此 Windows EXE 必须在 Windows 上构建，不能用 Linux 版本直接转换。若双击 EXE 没有反应，可在项目根目录执行下面的调试构建，让错误显示在控制台：

```bash
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --console --name DesktopStickyNotes-debug main.py
```

任务数据默认保存在：

```text
%LOCALAPPDATA%\DesktopStickyNotes\data.json
```

它不在 Git 仓库内。`data.json.bak` 是上一份有效备份。

## 项目结构

```text
desktop-sticky-notes/
├─ main.py
├─ requirements.txt
├─ requirements-build.txt
├─ build_exe.bat
├─ sticky_notes/
│  ├─ controller.py
│  ├─ desktop_windows.py
│  ├─ storage.py
│  ├─ task_service.py
│  ├─ task_statistics.py
│  ├─ themes.py
│  ├─ validators.py
│  ├─ models/task.py
│  └─ ui/
│     ├─ note_window.py
│     ├─ settings_dialog.py
│     └─ task_dialog.py
├─ tests/test_core.py
└─ practice/task_statistics.py
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## GitHub 第一次提交

先确认 Git 已安装，然后在项目根目录执行：

```bash
git init
git add .
git status
git commit -m "feat: 完成桌面便签 1.0"
```

在 GitHub 新建一个空仓库后，复制 GitHub 给出的远程地址：

```bash
git branch -M main
git remote add origin 你的仓库地址
git push -u origin main
```

以后一次功能修改对应一次 `git add` 和 `git commit`。不要把 `.venv`、任务数据、缓存或打包文件提交到 GitHub。

## 周子的代码贡献

`sticky_notes/task_statistics.py` 的 `calculate_daily_summary()` 由周子编写，已经通过审查并接入主窗口的完成数量与百分比计算。可用原练习入口复测：

```bash
python -m practice.task_statistics
```

正式源码保留了“周子编写，审查通过”的注释。

## Windows 实机验收

不同 Windows 版本对窗口层级的处理可能不同。请重点检查：

1. 打开浏览器后，浏览器位于便签上方。
2. 按 `Win+D` 后，便签仍在壁纸上方可见。
3. 打开添加、编辑或设置窗口时，对话框不会藏到其他窗口下面。
4. 移动便签、关闭并重启后，位置和任务仍然保留。

如果第 2 项在你的系统上不符合预期，需要进入下一阶段的 Windows 桌面 WorkerW 原生嵌入；当前版本使用 Qt 官方的窗口置底提示和 Windows `HWND_BOTTOM` 增强。
