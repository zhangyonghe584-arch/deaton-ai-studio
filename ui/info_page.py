from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine.case_service import CaseService
from engine.current_project import CurrentProject


FIELD_SECTIONS = (
    (
        "客户与地区",
        (("customer_name", "客户/案例名称"), ("customer_region", "客户地区")),
    ),
    (
        "车辆信息",
        (
            ("brand", "品牌"),
            ("model", "车型"),
            ("year", "年份"),
            ("vin", "VIN"),
            ("license_plate", "车牌"),
            ("mileage", "里程"),
            ("engine_model", "发动机/模块"),
        ),
    ),
    (
        "服务与结果",
        (
            ("fault_category", "故障分类"),
            ("fault_description", "故障描述"),
            ("service_type", "服务类型"),
            ("programming_type", "编程类型"),
            ("equipment_used", "使用设备"),
            ("repair_result", "维修结果"),
        ),
    ),
)


class InfoPage(QWidget):
    case_saved = Signal()

    def __init__(self):
        super().__init__()
        self.fields = {}

        layout = QVBoxLayout(self)
        title = QLabel("案例资料")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("案例信息会持续保存至当前案例的 project.json。"))

        for section_title, fields in FIELD_SECTIONS:
            group = QGroupBox(section_title)
            form = QFormLayout(group)
            for field, label in fields:
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(label)
                self.fields[field] = line_edit
                form.addRow(label, line_edit)
            layout.addWidget(group)

        notes_group = QGroupBox("技术备注")
        notes_layout = QVBoxLayout(notes_group)
        self.fields["technical_notes"] = QTextEdit()
        self.fields["technical_notes"].setPlaceholderText("记录诊断依据、编程步骤、注意事项或交付说明。")
        self.fields["technical_notes"].setMinimumHeight(100)
        notes_layout.addWidget(self.fields["technical_notes"])
        layout.addWidget(notes_group)

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
        for field, widget in self.fields.items():
            self._set_field_value(widget, info[field])
        self.status.setText("案例资料已加载。")

    def save(self):
        project_path = CurrentProject.get_project()
        if not project_path:
            self.status.setText("无法保存：尚未打开案例。")
            return

        values = {
            field: self._field_value(widget)
            for field, widget in self.fields.items()
        }
        CaseService(project_path).save_case_info(values)
        self.status.setText("已保存到当前案例。")
        self.case_saved.emit()

    @staticmethod
    def _field_value(widget):
        return widget.toPlainText() if isinstance(widget, QTextEdit) else widget.text()

    @staticmethod
    def _set_field_value(widget, value):
        if isinstance(widget, QTextEdit):
            widget.setPlainText(value)
        else:
            widget.setText(value)
