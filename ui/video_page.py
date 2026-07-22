from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout


class VideoPage(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        layout.addWidget(
            QLabel(
                "🎬 视频案例\n\n"
                "这里以后放视频上传和制作"
            )
        )

        self.setLayout(layout)