"""桌面便签启动入口。"""

import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from sticky_notes.controller import AppController
from sticky_notes.storage import TaskStorage


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("桌面便签")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ZhouziLearning")
    app.setStyle("Fusion")

    data_path = TaskStorage.default_data_path()
    try:
        data_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        QMessageBox.critical(None, "启动失败", f"无法创建数据目录：{error}")
        return 1

    # 防止同时打开两个进程，避免它们互相覆盖任务文件。
    instance_lock = QLockFile(str(data_path.with_suffix(".lock")))
    instance_lock.setStaleLockTime(0)
    if not instance_lock.tryLock(100):
        QMessageBox.information(None, "桌面便签", "桌面便签已经在运行。")
        return 0

    controller = AppController()
    app.aboutToQuit.connect(controller.shutdown)
    controller.start()
    exit_code = app.exec()
    instance_lock.unlock()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
