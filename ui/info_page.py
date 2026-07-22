from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout


class InfoPage(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        layout.addWidget(
            QLabel(
                "📝 案例信息\n\n"
                "这里以后放车型、故障分类等"
            )
        )

        self.setLayout(layout)