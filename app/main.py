import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.workbench import ApplicationWindow


def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("Deaton Auto Image Case Studio")
    window = ApplicationWindow()
    window.show()
    if os.getenv("DEATON_SMOKE_TEST") == "1":
        QTimer.singleShot(0, application.quit)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
