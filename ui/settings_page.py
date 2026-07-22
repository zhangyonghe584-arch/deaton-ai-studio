from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from PySide6.QtGui import QPixmap

from engine.brand_service import BrandService


class SettingsPage(QWidget):

    brand_saved = Signal()


    def __init__(self):

        super().__init__()

        self.brand_service = BrandService()

        self.fields = {}


        layout = QVBoxLayout(self)


        title = QLabel("品牌设置")
        title.setObjectName("pageTitle")

        layout.addWidget(title)


        layout.addWidget(
            QLabel(
                "用于所有 Deaton Auto 图片案例输出的品牌配置"
            )
        )


        # Logo区域

        logo_group = QGroupBox(
            "Logo管理"
        )


        logo_layout = QVBoxLayout(
            logo_group
        )


        self.logo_preview = QLabel(
            "暂无Logo"
        )

        self.logo_preview.setMinimumHeight(
            120
        )

        self.logo_preview.setScaledContents(
            True
        )


        logo_layout.addWidget(
            self.logo_preview
        )


        self.logo_button = QPushButton(
            "上传Logo"
        )

        self.logo_button.clicked.connect(
            self.upload_logo
        )


        logo_layout.addWidget(
            self.logo_button
        )


        layout.addWidget(
            logo_group
        )


        # 品牌信息

        group = QGroupBox(
            "品牌信息"
        )


        form = QFormLayout(
            group
        )


        for field, label in [

            ("name","品牌名称"),

            ("subtitle","品牌副标题"),

            ("primary_color","主色 #RRGGBB"),

            ("accent_color","强调色 #RRGGBB"),

        ]:


            edit = QLineEdit()

            edit.setPlaceholderText(
                label
            )

            self.fields[field] = edit


            form.addRow(
                label,
                edit
            )


        layout.addWidget(
            group
        )


        self.save_button = QPushButton(
            "保存品牌设置"
        )


        self.save_button.clicked.connect(
            self.save
        )


        layout.addWidget(
            self.save_button
        )


        self.status = QLabel()

        layout.addWidget(
            self.status
        )


        layout.addStretch()


        self.refresh()



    def refresh(self):

        profile = self.brand_service.load_profile()


        for field, edit in self.fields.items():

            edit.setText(
                profile.get(field,"")
            )


        logo = profile.get(
            "logo",
            ""
        )


        if logo:

            pixmap = QPixmap(
                logo
            )

            self.logo_preview.setPixmap(
                pixmap
            )

        else:

            self.logo_preview.setText(
                "暂无Logo"
            )



    def upload_logo(self):

        path, _ = QFileDialog.getOpenFileName(

            self,

            "选择Logo",

            "",

            "Images (*.png *.jpg *.jpeg *.svg)"

        )


        if not path:

            return


        result = self.brand_service.import_logo(
            path
        )


        if result:

            self.status.setText(
                "Logo上传成功"
            )

            self.refresh()

        else:

            self.status.setText(
                "Logo上传失败"
            )



    def save(self):

        try:

            self.brand_service.save_profile(

                {
                    key:value.text()

                    for key,value in self.fields.items()

                }

            )


            self.status.setText(
                "品牌设置已保存"
            )


            self.brand_saved.emit()


        except ValueError as error:

            self.status.setText(
                str(error)
            )