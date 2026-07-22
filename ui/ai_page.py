from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout


class AIPage(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        layout.addWidget(
            QLabel(
                "🤖 AI分析\n\n"
                "这里以后连接API"
            )
        )

        self.setLayout(layout)