from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QWidget


class VideoPage(QWidget):
    """Reserves the production workspace without implementing video processing."""

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        title = QLabel("视频案例制作")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("已预留视频案例制作布局；视频导入、剪辑与渲染将在后续阶段接入。"))

        workspace = QGridLayout()
        workspace.setHorizontalSpacing(16)
        workspace.setVerticalSpacing(16)
        workspace.addWidget(
            self.placeholder_group(
                "视频素材",
                "主视频素材\n\n未来：从当前案例的视频目录导入、整理和选择主片段。",
            ),
            0,
            0,
        )
        workspace.addWidget(
            self.placeholder_group(
                "成片预览",
                "成片画面预览\n\n未来：显示品牌片头、字幕、案例画面与最终导出效果。",
            ),
            0,
            1,
        )
        workspace.addWidget(
            self.placeholder_group(
                "案例故事板",
                "01 车辆与问题  →  02 诊断过程  →  03 编程服务  →  04 完成结果\n\n未来：自动从现有案例资料和六类素材生成可编辑故事板。",
            ),
            1,
            0,
            1,
            2,
        )
        workspace.setColumnStretch(0, 1)
        workspace.setColumnStretch(1, 1)
        workspace.setRowStretch(0, 1)
        workspace.setRowStretch(1, 1)
        layout.addLayout(workspace, 1)

        notice = QLabel("当前为布局占位，尚未启用视频导入、时间线编辑或导出功能。")
        notice.setObjectName("statusLabel")
        layout.addWidget(notice)

    @staticmethod
    def placeholder_group(title, text):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setMinimumHeight(190)
        placeholder.setObjectName("videoPlaceholder")
        group_layout.addWidget(placeholder)
        return group
