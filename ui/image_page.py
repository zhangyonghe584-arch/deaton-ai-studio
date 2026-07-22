import os

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.case_service import ASSET_STATUSES, CaseService
from engine.current_project import CurrentProject
from engine.image_manager import CATEGORY_MAP, ImageManager
from engine.image_renderer import ImageCaseRenderer


class DropBox(QFrame):
    asset_selected = Signal(dict)
    assets_changed = Signal()

    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self._refreshing = False
        self.setAcceptDrops(True)
        self.setObjectName("assetCard")
        self.setMinimumHeight(330)

        layout = QVBoxLayout(self)
        self.title = QLabel(category_name)
        self.title.setObjectName("assetTitle")
        layout.addWidget(self.title)

        self.asset_list = QListWidget()
        self.asset_list.setIconSize(QSize(72, 54))
        self.asset_list.setMinimumHeight(140)
        self.asset_list.itemSelectionChanged.connect(self._emit_selected_asset)
        layout.addWidget(self.asset_list)

        import_layout = QHBoxLayout()
        self.import_button = QPushButton("选择图片")
        self.import_button.clicked.connect(self.select_files)
        import_layout.addWidget(self.import_button)
        self.count_label = QLabel("0 张")
        import_layout.addWidget(self.count_label)
        import_layout.addStretch()
        layout.addLayout(import_layout)

        action_layout = QHBoxLayout()
        self.move_up_button = QPushButton("上移")
        self.move_down_button = QPushButton("下移")
        self.primary_button = QPushButton("设为主图")
        self.replace_button = QPushButton("替换")
        self.delete_button = QPushButton("删除")
        for button, callback in (
            (self.move_up_button, self.move_selected_up),
            (self.move_down_button, self.move_selected_down),
            (self.primary_button, self.set_primary),
            (self.replace_button, self.replace_selected),
            (self.delete_button, self.delete_selected),
        ):
            button.clicked.connect(callback)
            action_layout.addWidget(button)
        layout.addLayout(action_layout)

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(ASSET_STATUSES)
        self.status_combo.currentTextChanged.connect(self.change_status)
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)

        self.status = QLabel("拖放图片到这里")
        self.status.setObjectName("statusLabel")
        layout.addWidget(self.status)
        self._set_asset_actions_enabled(False)

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

    def refresh(self, selected_asset_id=None):
        self._refreshing = True
        self.asset_list.clear()
        project_path = CurrentProject.get_project()
        self.import_button.setEnabled(bool(project_path))
        if not project_path:
            self.count_label.setText("0 张")
            self._set_asset_actions_enabled(False)
            self._refreshing = False
            return

        assets = CaseService(project_path).list_assets(self.category_name)
        for asset in assets:
            item = QListWidgetItem(asset["original_filename"])
            item.setData(Qt.UserRole, asset)
            item.setToolTip(self._asset_tooltip(asset))
            pixmap = QPixmap(os.path.join(project_path, asset["path"]))
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap.scaled(72, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            self.asset_list.addItem(item)
            if asset["id"] == selected_asset_id:
                self.asset_list.setCurrentItem(item)
        self.count_label.setText(f"{len(assets)} 张")
        self._refreshing = False
        self._emit_selected_asset()

    def _emit_selected_asset(self):
        selected = self.selected_asset()
        self._set_asset_actions_enabled(selected is not None)
        if selected is None:
            return
        self._refreshing = True
        self.status_combo.setCurrentText(selected.get("status", ASSET_STATUSES[0]))
        self._refreshing = False
        self.asset_selected.emit(selected)

    def selected_asset(self):
        selected = self.asset_list.selectedItems()
        return selected[0].data(Qt.UserRole) if selected else None

    def move_selected_up(self):
        self._move_selected(-1)

    def move_selected_down(self):
        self._move_selected(1)

    def _move_selected(self, offset):
        asset = self.selected_asset()
        if asset is None:
            return
        assets = CaseService(CurrentProject.get_project()).list_assets(self.category_name)
        asset_ids = [item["id"] for item in assets]
        index = asset_ids.index(asset["id"])
        target = index + offset
        if target < 0 or target >= len(asset_ids):
            return
        asset_ids[index], asset_ids[target] = asset_ids[target], asset_ids[index]
        CaseService(CurrentProject.get_project()).reorder_assets(self.category_name, asset_ids)
        self.refresh(asset["id"])
        self.assets_changed.emit()

    def set_primary(self):
        asset = self.selected_asset()
        if asset is None:
            return
        CaseService(CurrentProject.get_project()).set_primary_asset(asset["id"])
        self.refresh(asset["id"])
        self.status.setText("已设为主图")
        self.assets_changed.emit()

    def change_status(self, status):
        asset = self.selected_asset()
        if self._refreshing or asset is None:
            return
        CaseService(CurrentProject.get_project()).set_asset_status(asset["id"], status)
        self.refresh(asset["id"])
        self.status.setText(f"素材状态已更新为：{status}")
        self.assets_changed.emit()

    def replace_selected(self):
        asset = self.selected_asset()
        if asset is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择替换图片",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if not path:
            return
        result = ImageManager(CurrentProject.get_project()).replace_image(asset["id"], path)
        self.refresh(asset["id"])
        self.status.setText("素材已替换" if result.success else f"替换失败：{result.error}")
        self.assets_changed.emit()

    def delete_selected(self):
        asset = self.selected_asset()
        if asset is None:
            return
        answer = QMessageBox.question(
            self,
            "删除素材",
            f"确定删除“{asset['original_filename']}”吗？此操作会移除项目内的图片文件。",
        )
        if answer != QMessageBox.Yes:
            return
        deleted = ImageManager(CurrentProject.get_project()).delete_image(asset["id"])
        self.refresh()
        self.status.setText("素材已删除" if deleted else "删除素材失败")
        self.assets_changed.emit()

    def _set_asset_actions_enabled(self, enabled):
        for button in (
            self.move_up_button,
            self.move_down_button,
            self.primary_button,
            self.replace_button,
            self.delete_button,
            self.status_combo,
        ):
            button.setEnabled(enabled)

    @staticmethod
    def _asset_tooltip(asset):
        primary = "主图" if asset.get("is_primary") else "普通素材"
        return f"{asset['original_filename']}\n{primary} · {asset.get('status', '待整理')}"


class ImagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_asset = None
        self.boxes = []

        layout = QVBoxLayout(self)
        title = QLabel("图片案例制作")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("导入、整理和审核六类素材；选择车辆外观主图后即可生成案例封面。"))

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
        panel_layout.addWidget(QLabel("选择发布模板；系统优先使用车辆外观主图。"))
        self.template_combo = QComboBox()
        for template in ImageCaseRenderer(CurrentProject.get_project()).list_templates():
            self.template_combo.addItem(
                f"{template['name']} · {template['description']}",
                template["id"],
            )
        panel_layout.addWidget(self.template_combo)

        self.preview = QLabel("选择“车辆外观”中的素材")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(240)
        self.preview.setObjectName("preview")
        panel_layout.addWidget(self.preview)

        self.selection_label = QLabel("未选择时会自动使用车辆外观主图。")
        panel_layout.addWidget(self.selection_label)
        self.render_button = QPushButton("生成当前模板")
        self.render_button.clicked.connect(self.render_selected_template)
        panel_layout.addWidget(self.render_button)
        self.render_all_button = QPushButton("一键生成全部 3 张")
        self.render_all_button.clicked.connect(self.render_all_templates)
        panel_layout.addWidget(self.render_all_button)
        self.export_status = QLabel("导出记录会保存在当前案例中。")
        self.export_status.setWordWrap(True)
        self.export_status.setObjectName("statusLabel")
        panel_layout.addWidget(self.export_status)
        panel_layout.addStretch()
        workspace.addWidget(production_panel, 1)
        layout.addLayout(workspace)
        self.refresh()

    def refresh(self):
        selected_id = self.selected_asset["id"] if self.selected_asset else None
        for box in self.boxes:
            box.refresh(selected_id if box.category_name == self._selected_category() else None)
        if self.selected_asset:
            project_path = CurrentProject.get_project()
            asset = CaseService(project_path).get_asset(selected_id) if project_path else None
            if asset is None:
                self.selected_asset = None
                self.preview.clear()
                self.preview.setText("选择“车辆外观”中的素材")
                self.selection_label.setText("未选择时会自动使用车辆外观主图。")
            else:
                self.selected_asset = asset

    def select_asset(self, asset):
        self.selected_asset = asset
        self.selection_label.setText(
            f"{asset['original_filename']} · {'主图' if asset.get('is_primary') else asset.get('status', '待整理')}"
        )
        project_path = CurrentProject.get_project()
        image_path = os.path.join(project_path, asset["path"])
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.preview.setText("无法预览图片")
            return
        self.preview.setPixmap(pixmap.scaled(250, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.export_status.setText("已选择素材；未选择车辆外观时系统将自动使用主图。")

    def render_selected_template(self):
        project_path = CurrentProject.get_project()
        if not project_path:
            self.export_status.setText("请先打开案例。")
            return
        asset_id = (
            self.selected_asset["id"]
            if self.selected_asset and self.selected_asset["category"] == "01 车辆外观"
            else None
        )
        result = ImageCaseRenderer(project_path).render(
            self.template_combo.currentData(),
            asset_id,
        )
        if result.success:
            self.export_status.setText(f"模板已生成：{result.output_path}")
        else:
            self.export_status.setText(f"生成失败：{result.error}")

    def render_all_templates(self):
        project_path = CurrentProject.get_project()
        if not project_path:
            self.export_status.setText("请先打开案例。")
            return
        asset_id = (
            self.selected_asset["id"]
            if self.selected_asset and self.selected_asset["category"] == "01 车辆外观"
            else None
        )
        results = ImageCaseRenderer(project_path).render_all(asset_id)
        successful = [result for result in results if result.success]
        failed = [result for result in results if not result.success]
        if failed:
            self.export_status.setText(f"已生成 {len(successful)} 张；失败：{failed[0].error}")
        else:
            self.export_status.setText(f"已生成 {len(successful)} 张发布图片。")

    def _selected_category(self):
        return self.selected_asset["category"] if self.selected_asset else None
