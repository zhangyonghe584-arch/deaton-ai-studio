from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QFrame
)

from PySide6.QtCore import Qt

from engine.image_manager import ImageManager
from engine.current_project import CurrentProject



class DropBox(QFrame):

    def __init__(self, title):

        super().__init__()

        self.title = title

        self.files = []


        # 开启拖拽

        self.setAcceptDrops(True)


        self.setMinimumHeight(
            160
        )


        self.setFrameShape(
            QFrame.Box
        )


        self.label = QLabel(
            f"{title}\n\n拖入图片"
        )


        self.label.setAlignment(
            Qt.AlignCenter
        )


        layout = QVBoxLayout()

        layout.addWidget(
            self.label
        )


        self.setLayout(
            layout
        )



    # 鼠标进入拖拽区域

    def dragEnterEvent(self, event):

        print("进入区域")


        if event.mimeData().hasUrls():

            event.acceptProposedAction()



    # 拖动经过区域

    def dragMoveEvent(self, event):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()



    # 松开鼠标

    def dropEvent(self, event):

        print("收到文件")


        urls = event.mimeData().urls()


        print(
            "数量:",
            len(urls)
        )


        project_path = CurrentProject.get_project()


        print(
            "当前项目:",
            project_path
        )


        if not project_path:

            self.label.setText(
                f"{self.title}\n\n没有当前项目"
            )

            return



        manager = ImageManager(
            project_path
        )


        count = 0


        for url in urls:


            path = url.toLocalFile()


            print(
                "文件:",
                path
            )


            if path.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                    ".bmp"
                )
            ):


                result = manager.save_image(
                    path,
                    self.title
                )


                print(
                    "保存:",
                    result
                )


                if result:

                    self.files.append(
                        path
                    )

                    count += 1



        self.label.setText(

            f"{self.title}\n\n"
            f"已添加 {count} 张"

        )





class ImagePage(QWidget):


    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        title = QLabel(
            "📷 图片案例素材"
        )


        title.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            """
        )


        layout.addWidget(
            title
        )



        grid = QGridLayout()


        categories = [

            "01 车辆外观",

            "02 故障现象",

            "03 诊断过程",

            "04 编程过程",

            "05 完成结果",

            "06 技术资料"

        ]


        for i, name in enumerate(categories):

            box = DropBox(
                name
            )


            grid.addWidget(
                box,
                i // 3,
                i % 3
            )


        layout.addLayout(
            grid
        )


        self.setLayout(
            layout
        )