import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.case_service import CaseService
from engine.current_project import CurrentProject
from engine.image_manager import CATEGORY_MAP, ImageManager
from engine.image_renderer import ImageCaseRenderer


class DropBox(QFrame):
    asset_selected = Signal(dict)
    assets_changed = Signal()

    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self.setAcceptDrops(True)
        self.setObjectName("assetCard")
        self.setMinimumHeight(230)

        layout = QVBoxLayout(self)
        self.title = QLabel(category_name)
        self.title.setObjectName("assetTitle")
        layout.addWidget(self.title)

        self.asset_list = QListWidget()
        self.asset_list.setMaximumHeight(116)
        self.asset_list.itemSelectionChanged.connect(self._emit_selected_asset)
        layout.addWidget(self.asset_list)

        button_layout = QHBoxLayout()
        self.import_button = QPushButton("选择图片")
        self.import_button.clicked.connect(self.select_files)
        button_layout.addWidget(self.import_button)
        self.count_label = QLabel("0 张")
        button_layout.addWidget(self.count_label)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.status = QLabel("拖放图片到这里")
        self.status.setObjectName("statusLabel")
        layout.addWidget(self.status)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.import_paths(paths)
        event.acceptProposedAction()

    def select_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择案例图片",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        self.import_paths(paths)

    def import_paths(self, paths):
        project_path = CurrentProject.get_project()
        if not project_path:
            self.status.setText("没有当前案例")
            return

        manager = ImageManager(project_path)
        imported = 0
        errors = []
        for path in paths:
            result = manager.import_image(path, self.category_name)
            if result.success:
                imported += 1
            else:
                errors.append(result.error)

        self.refresh()
        if errors:
            self.status.setText("导入失败：" + "；".join(sorted(set(errors))))
        elif imported:
            self.status.setText(f"已导入 {imported} 张图片")
        self.assets_changed.emit()

    def refresh(self):
        self.asset_list.clear()
        project_path = CurrentProject.get_project()
        self.import_button.setEnabled(bool(project_path))
        if not project_path:
            self.count_label.setText("0 张")
            return

        assets = CaseService(project_path).list_assets(self.category_name)
        for asset in assets:
            item = QListWidgetItem(asset["original_filename"])
            item.setData(Qt.UserRole, asset)
            self.asset_list.addItem(item)
        self.count_label.setText(f"{len(assets)} 张")

    def _emit_selected_asset(self):
        selected = self.asset_list.selectedItems()
        if selected:
            self.asset_selected.emit(selected[0].data(Qt.UserRole))


class ImagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_asset = None
        self.boxes = []

        layout = QVBoxLayout(self)
        title = QLabel("图片案例制作")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("按分类导入案例素材，选择一张车辆外观图，即可生成固定版式案例封面。"))

        workspace = QHBoxLayout()
        grid = QGridLayout()
        for index, category_name in enumerate(CATEGORY_MAP):
            box = DropBox(category_name)
            box.asset_selected.connect(self.select_asset)
            box.assets_changed.connect(self.refresh)
            self.boxes.append(box)
            grid.addWidget(box, index // 3, index % 3)
        workspace.addLayout(grid, 3)

        production_panel = QFrame()
        production_panel.setObjectName("productionPanel")
        production_panel.setMinimumWidth(280)
        panel_layout = QVBoxLayout(production_panel)
        panel_title = QLabel("图片成品")
        panel_title.setObjectName("panelTitle")
        panel_layout.addWidget(panel_title)
        panel_layout.addWidget(QLabel("模板：案例封面 · 1080 × 1350"))

        self.preview = QLabel("选择“车辆外观”中的素材")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(240)
        self.preview.setObjectName("preview")
        panel_layout.addWidget(self.preview)

        self.selection_label = QLabel("尚未选择素材")
        panel_layout.addWidget(self.selection_label)
        self.render_button = QPushButton("生成案例封面")
        self.render_button.setEnabled(False)
        self.render_button.clicked.connect(self.render_cover)
        panel_layout.addWidget(self.render_button)
        self.export_status = QLabel("导出记录会保存在当前案例中。")
        self.export_status.setWordWrap(True)
        self.export_status.setObjectName("statusLabel")
        panel_layout.addWidget(self.export_status)
        panel_layout.addStretch()
        workspace.addWidget(production_panel, 1)
        layout.addLayout(workspace)
        self.refresh()

    def refresh(self):
        for box in self.boxes:
            box.refresh()
        if self.selected_asset:
            project_path = CurrentProject.get_project()
            asset = CaseService(project_path).get_asset(self.selected_asset["id"]) if project_path else None
            if asset is None:
                self.selected_asset = None
                self.preview.clear()
                self.preview.setText("选择“车辆外观”中的素材")
                self.selection_label.setText("尚未选择素材")
                self.render_button.setEnabled(False)

    def select_asset(self, asset):
        self.selected_asset = asset
        self.selection_label.setText(asset["original_filename"])
        self.render_button.setEnabled(asset["category"] == "01 车辆外观")
        project_path = CurrentProject.get_project()
        image_path = os.path.join(project_path, asset["path"])
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.preview.setText("无法预览图片")
            return
        self.preview.setPixmap(pixmap.scaled(250, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.export_status.setText("已选择素材；使用车辆外观图片可生成封面。")

    def render_cover(self):
        project_path = CurrentProject.get_project()
        if not project_path or not self.selected_asset:
            self.export_status.setText("请先选择车辆外观素材。")
            return

        result = ImageCaseRenderer(project_path).render("case_cover", self.selected_asset["id"])
        if result.success:
            self.export_status.setText(f"封面已生成：{result.output_path}")
        else:
            self.export_status.setText(f"生成失败：{result.error}")
