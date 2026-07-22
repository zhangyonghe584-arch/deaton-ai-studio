from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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
        layout.addWidget(QLabel("用于所有图片案例的固定发布识别，不影响已有案例资料。"))

        group = QGroupBox("品牌档案")
        form = QFormLayout(group)
        for field, label in (
            ("name", "品牌名称"),
            ("subtitle", "品牌副标题"),
            ("primary_color", "主色 #RRGGBB"),
            ("accent_color", "强调色 #RRGGBB"),
        ):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(label)
            self.fields[field] = line_edit
            form.addRow(label, line_edit)
        layout.addWidget(group)

        self.save_button = QPushButton("保存品牌设置")
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)
        self.status = QLabel()
        self.status.setObjectName("statusLabel")
        layout.addWidget(self.status)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        profile = self.brand_service.load_profile()
        for field, line_edit in self.fields.items():
            line_edit.setText(profile[field])
        self.status.setText("品牌设置已加载。")

    def save(self):
        try:
            self.brand_service.save_profile(
                {field: line_edit.text() for field, line_edit in self.fields.items()}
            )
        except ValueError as error:
            self.status.setText(f"无法保存：{error}")
            return
        self.status.setText("品牌设置已保存，将用于新的图片输出。")
        self.brand_saved.emit()
