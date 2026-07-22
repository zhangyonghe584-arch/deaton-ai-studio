from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.case_service import CASE_INFO_FIELDS, CaseService
from engine.current_project import CurrentProject


FIELD_LABELS = {
    "brand": "品牌",
    "model": "车型",
    "year": "年份",
    "region": "地区",
    "fault_category": "故障类别",
    "service_type": "服务类型",
    "programming_type": "编程类型",
    "equipment_used": "使用设备",
    "repair_result": "维修结果",
}


class InfoPage(QWidget):
    case_saved = Signal()

    def __init__(self):
        super().__init__()
        self.fields = {}

        layout = QVBoxLayout(self)
        title = QLabel("案例资料")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("填写基础信息后，系统会将其写入当前案例的 project.json。"))

        form = QFormLayout()
        for field in CASE_INFO_FIELDS:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(FIELD_LABELS[field])
            self.fields[field] = line_edit
            form.addRow(FIELD_LABELS[field], line_edit)
        layout.addLayout(form)

        self.save_button = QPushButton("保存案例资料")
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)

        self.status = QLabel()
        self.status.setObjectName("statusLabel")
        layout.addWidget(self.status)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        project_path = CurrentProject.get_project()
        enabled = bool(project_path)
        self.save_button.setEnabled(enabled)
        if not enabled:
            self.status.setText("尚未打开案例。")
            return

        info = CaseService(project_path).load_case_info()
        for field, line_edit in self.fields.items():
            line_edit.setText(info[field])
        self.status.setText("案例资料已加载。")

    def save(self):
        project_path = CurrentProject.get_project()
        if not project_path:
            self.status.setText("无法保存：尚未打开案例。")
            return

        values = {field: line_edit.text() for field, line_edit in self.fields.items()}
        CaseService(project_path).save_case_info(values)
        self.status.setText("已保存到当前案例。")
        self.case_saved.emit()
