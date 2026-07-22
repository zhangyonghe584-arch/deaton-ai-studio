from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget
)

from ui.image_page import ImagePage
from ui.video_page import VideoPage
from ui.info_page import InfoPage
from ui.ai_page import AIPage
from ui.settings_page import SettingsPage
from engine.project_manager import ProjectManager
from engine.current_project import CurrentProject


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        manager = ProjectManager()

        project_path = manager.create_new_case()

        CurrentProject.set_project(
            project_path
        )

        self.setWindowTitle(
            "Deaton AI Studio"
        )

        self.resize(
            1400,
            850
        )

        self.init_ui()



    def init_ui(self):

        main = QWidget()

        self.setCentralWidget(main)



        # 左侧菜单

        menu_layout = QVBoxLayout()


        title = QLabel(
            "Deaton AI Studio"
        )

        title.setStyleSheet(
            """
            font-size:22px;
            font-weight:bold;
            padding:20px;
            """
        )


        menu_layout.addWidget(title)



        buttons = [
            ("📷 图片案例",0),
            ("🎬 视频案例",1),
            ("📝 案例信息",2),
            ("🤖 AI分析",3),
            ("⚙ 设置",4)
        ]


        for text,index in buttons:

            btn = QPushButton(text)

            btn.setMinimumHeight(45)

            btn.clicked.connect(
                lambda checked=False,i=index:
                self.pages.setCurrentIndex(i)
            )

            menu_layout.addWidget(btn)



        menu_layout.addStretch()



        left = QWidget()

        left.setLayout(
            menu_layout
        )

        left.setFixedWidth(
            230
        )



        # 页面区域


        self.pages = QStackedWidget()

        self.image_page = ImagePage()
        self.info_page = InfoPage()
        self.info_page.case_saved.connect(self.image_page.refresh)

        self.pages.addWidget(
            self.image_page
        )

        self.pages.addWidget(
            VideoPage()
        )

        self.pages.addWidget(
            self.info_page
        )

        self.pages.addWidget(
            AIPage()
        )

        self.pages.addWidget(
            SettingsPage()
        )



        layout = QHBoxLayout()

        layout.addWidget(left)

        layout.addWidget(
            self.pages
        )

        main.setLayout(layout)
        self.pages.setCurrentIndex(2)
