from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout


class SettingsPage(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        layout.addWidget(
            QLabel(
                "⚙ 设置\n\n"
                "API、Logo、模板管理"
            )
        )

        self.setLayout(layout)