from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt, Signal, QSettings
from PySide6.QtCore import QStringListModel
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QCompleter,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.ai_plan import OpenAIPlanService
from core.ai_memory import ProjectMemory
from core.case_store import CaseStore
from core.constants import CASE_FIELDS, SLOT_SPECS
from core.generation import LocalGenerationService


STYLE = """
QWidget { background: #F6F3ED; color: #22272B; font-family: 'Segoe UI'; font-size: 14px; }
QMainWindow { background: #F6F3ED; }
QLabel#kicker { color: #C76023; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #18222C; font-size: 28px; font-weight: 700; }
QLabel#subtitle { color: #677077; font-size: 13px; }
QFrame#panel, QFrame#slot { background: #FCFBF8; border: 1px solid #D9DBD9; border-radius: 12px; }
QFrame#slot:hover { border: 2px solid #123B68; }
QPushButton { background: #123B68; color: #FFFFFF; border: 0; border-radius: 7px; font-weight: 600; padding: 10px 16px; }
QPushButton:hover { background: #0C2E54; }
QPushButton:disabled { background: #BFC4C5; }
QPushButton#secondary { background: #E5E7E5; color: #26323D; }
QPushButton#step { background: transparent; color: #56616A; text-align: left; border-radius: 8px; padding: 12px; }
QPushButton#step:checked { background: #E1EAF1; color: #123B68; }
QLineEdit, QComboBox, QPlainTextEdit { background: #FFFFFF; border: 1px solid #CDD1D0; border-radius: 6px; padding: 8px; selection-background-color: #123B68; }
QComboBox::drop-down { border: 0; width: 28px; }
QCheckBox { spacing: 8px; }
QScrollArea { border: 0; }
"""


class VisibleArrowComboBox(QComboBox):
    """Editable combo box with a theme-independent, always-visible arrow."""

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        x = self.width() - 18
        y = self.height() // 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#123B68"))
        painter.drawPolygon(QPolygon([QPoint(x - 5, y - 2), QPoint(x + 5, y - 2), QPoint(x, y + 4)]))

    def mousePressEvent(self, event):
        if event.position().x() >= self.width() - 36:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)


class SlotCard(QFrame):
    asset_dropped = Signal(str, Path)

    def __init__(self, key: str, label: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("slot")
        self.setAcceptDrops(True)
        self.setMinimumSize(235, 215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.image = QLabel(alignment=Qt.AlignCenter)
        self.image.setFixedHeight(135)
        self.image.setStyleSheet("background: #EEF0EE; border-radius: 7px; color: #7A8389;")
        self.caption = QLabel(label)
        self.caption.setStyleSheet("font-weight: 700; color: #283641;")
        self.note = QLabel("拖放一张图片，或点击选择")
        self.note.setStyleSheet("font-size: 11px; color: #7A8389;")
        layout.addWidget(self.image, 1)
        layout.addWidget(self.caption)
        layout.addWidget(self.note)

    def set_image(self, path: Path | None) -> None:
        if path and path.is_file():
            pixmap = QPixmap(str(path))
            self.image.setPixmap(pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.note.setText(path.name)
        else:
            self.image.setPixmap(QPixmap())
            self.image.setText("空槽位")
            self.note.setText("拖放一张图片，或点击选择")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        pixmap = self.image.pixmap()
        if pixmap:
            self.image.setPixmap(pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(self, "选择图片", filter="Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)")
            if path:
                self.asset_dropped.emit(self.key, Path(path))
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.asset_dropped.emit(self.key, Path(urls[0].toLocalFile()))
            event.acceptProposedAction()


class WorkbenchPage(QWidget):
    def __init__(self, store: CaseStore, case_dir: Path):
        super().__init__()
        self.store = store
        self.case_dir = case_dir
        self.generator = LocalGenerationService(store)
        self.manifest = self.store.load(case_dir)
        self.slot_cards: dict[str, SlotCard] = {}
        self.fields: dict[str, QComboBox] = {}
        self.model_catalog: dict[str, list[str]] = {}
        self.step_group = QButtonGroup(self)
        self._build()
        self._load_manifest()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        sidebar = QFrame(objectName="panel")
        sidebar.setFixedWidth(215)
        sidebar_layout = QVBoxLayout(sidebar)
        brand = QLabel("DEATON AUTO")
        brand.setStyleSheet("font-weight: 800; color: #123B68; font-size: 17px;")
        side_title = QLabel("图片案例工作台")
        side_title.setStyleSheet("font-size: 12px; color: #6A747B;")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(side_title)
        sidebar_layout.addSpacing(28)
        for index, title in enumerate(("1. 素材", "2. 案例信息", "3. 人工智能方案", "4. 生成与保存")):
            button = QPushButton(title, objectName="step", checkable=True)
            button.clicked.connect(lambda checked, page=index: self.pages.setCurrentIndex(page))
            self.step_group.addButton(button, index)
            sidebar_layout.addWidget(button)
        sidebar_layout.addStretch()
        root.addWidget(sidebar)
        main = QVBoxLayout()
        self.case_label = QLabel()
        self.case_label.setObjectName("kicker")
        self.page_title = QLabel("素材")
        self.page_title.setObjectName("title")
        main.addWidget(self.case_label)
        main.addWidget(self.page_title)
        self.pages = QStackedWidget()
        self.pages.currentChanged.connect(self._update_step)
        self.pages.addWidget(self._asset_page())
        self.pages.addWidget(self._info_page())
        self.pages.addWidget(self._ai_page())
        self.pages.addWidget(self._generation_page())
        main.addWidget(self.pages, 1)
        root.addLayout(main, 1)
        self.step_group.button(0).setChecked(True)

    def _asset_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        instruction = QLabel("固定 6 个素材位置，每个位置放 1 张图片即可；没有图片的位置可以留空。")
        instruction.setObjectName("subtitle")
        layout.addWidget(instruction)
        grid = QGridLayout()
        grid.setSpacing(14)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        for index, (key, label) in enumerate(SLOT_SPECS):
            card = SlotCard(key, label)
            card.asset_dropped.connect(self._set_asset)
            self.slot_cards[key] = card
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def _info_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel("这里只填写已经完成、可以公开展示的案例事实。不要填写等待连接、待确认、进一步诊断等过程状态。下拉选项统一显示为“英文 / 中文”；没有合适选项时可以直接输入中文，生成图片时会自动整理为英文。")
        note.setObjectName("subtitle")
        card = QFrame(objectName="panel")
        form = QFormLayout(card)
        form.setContentsMargins(28, 28, 28, 28)
        options = self.store.options()
        self.model_catalog = self.store.model_options()
        sections = {
            "车辆信息": {"brand", "model", "year", "mileage", "location"},
            "客户问题与诊断": {"customer_issue", "fault_category", "dtc_codes", "diagnosis"},
            "已完成的远程服务": {"service", "programming", "programming_detail", "equipment"},
            "修复结果与验证": {"result", "final_status", "verification", "contact", "website"},
        }
        section_for = {key: title for title, keys in sections.items() for key in keys}
        current_section = ""
        for key, label in CASE_FIELDS:
            # 使用安全回退，避免以后新增字段忘记加入分组时导致程序启动崩溃。
            section = section_for.get(key, "其他案例信息")
            if section != current_section:
                current_section = section
                heading = QLabel(current_section)
                heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #123B68; padding-top: 12px;")
                form.addRow(heading)
            combo = VisibleArrowComboBox(editable=True)
            combo.setPlaceholderText(self._field_placeholder(key))
            if key != "model":
                combo.addItems(options.get(key, []))
            combo.setInsertPolicy(QComboBox.NoInsert)
            completer = QCompleter(combo.model(), combo)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            combo.setCompleter(completer)
            combo.setCurrentText("")
            combo.editTextChanged.connect(self._save_information)
            if key == "brand":
                combo.currentTextChanged.connect(self._brand_changed)
            self.fields[key] = combo
            form.addRow(f"{label}", combo)
        layout.addWidget(note)
        layout.addSpacing(8)
        scroll = QScrollArea(widgetResizable=True)
        scroll.setWidget(card)
        layout.addWidget(scroll, 1)
        layout.addStretch()
        return page

    @staticmethod
    def _field_placeholder(key: str) -> str:
        return {
            "brand": "请选择或输入品牌",
            "model": "请选择或输入车型",
            "year": "请选择或输入年份",
            "mileage": "例如：69664 km",
            "location": "请选择国家 + 省份 / 州 / 地区，例如：United States / Alaska / 美国 / 阿拉斯加",
            "customer_issue": "例如：客户反馈自适应巡航无法使用",
            "fault_category": "请选择主要故障类别",
            "diagnosis": "例如：扫描发现模块编码和组件保护异常",
            "programming_detail": "例如：完成模块编码、组件保护处理和匹配学习",
            "final_status": "请选择已完成的案例结论",
            "dtc_codes": "例如：U110100、U112100",
            "equipment": "例如：ODIS / 原厂诊断设备",
            "verification": "例如：最终扫描通过，功能测试正常",
            "contact": "例如：WhatsApp +86 138 9855 2107",
            "website": "例如：https://deatonauto.com",
        }.get(key, "请选择或输入")

    def _ai_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        warning = QLabel("AI 分析是可选的。关闭时可直接按案例信息和素材生成；开启后才会先分析方案。已有 1–5 张案例图都可以分析，Logo 会一并作为参考。")
        warning.setObjectName("subtitle")
        layout.addWidget(warning)
        selector = QFrame(objectName="panel")
        selector_layout = QVBoxLayout(selector)
        selector_layout.setContentsMargins(20, 20, 20, 20)
        self.use_ai = QCheckBox("启用 AI 分析（可选）")
        self.use_ai.setToolTip("关闭：跳过 AI，直接生成图片；开启：先分析并确认 AI 方案")
        self.use_ai.toggled.connect(self._ai_mode_changed)
        selector_layout.addWidget(self.use_ai)
        self.ai_mode_label = QLabel()
        self.ai_mode_label.setObjectName("subtitle")
        selector_layout.addWidget(self.ai_mode_label)
        selector_layout.addWidget(QLabel("勾选要交给 AI 分析的案例图片（1–5 张；Logo 会自动一并分析）"))
        self.ai_checks: dict[str, QCheckBox] = {}
        for key, label in SLOT_SPECS:
            if key != "logo":
                check = QCheckBox(label)
                check.setChecked(True)
                self.ai_checks[key] = check
                selector_layout.addWidget(check)
        self.analyze_button = QPushButton("分析图片和案例信息")
        self.analyze_button.clicked.connect(self._analyze)
        selector_layout.addWidget(self.analyze_button)
        self.plan_editor = QPlainTextEdit(placeholderText="分析方案会显示在这里。你可以自行修改，再确认用于本地生成。")
        self.plan_editor.textChanged.connect(self._plan_changed)
        self.confirm_plan = QCheckBox("确认使用这份方案进行生成")
        self.confirm_plan.toggled.connect(self._plan_changed)
        layout.addWidget(selector)
        layout.addSpacing(12)
        layout.addWidget(QLabel("AI 方案（可以修改）", objectName="title"))
        layout.addWidget(self.plan_editor, 1)
        self.confirm_plan.setText("确认使用这份方案生成图片")
        layout.addWidget(self.confirm_plan)
        return page

    def _generation_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel("生成使用本机 Pillow 脚本，最终输出 5 张 1080×1920 图片。")
        note.setObjectName("subtitle")
        self.save_path_label = QLabel()
        self.save_path_label.setObjectName("subtitle")
        actions = QHBoxLayout()
        self.generate_button = QPushButton("本地生成预览")
        self.generate_button.clicked.connect(self._generate)
        save_button = QPushButton("保存", objectName="secondary")
        save_button.clicked.connect(self._save_output)
        change_path_button = QPushButton("更改保存路径", objectName="secondary")
        change_path_button.clicked.connect(self._change_save_path)
        actions.addWidget(self.generate_button)
        actions.addWidget(save_button)
        actions.addWidget(change_path_button)
        actions.addStretch()
        self.preview_layout = QGridLayout()
        preview_content = QWidget()
        preview_content.setLayout(self.preview_layout)
        scroll = QScrollArea(widgetResizable=True)
        scroll.setWidget(preview_content)
        layout.addWidget(note)
        layout.addWidget(self.save_path_label)
        layout.addLayout(actions)
        layout.addWidget(scroll, 1)
        return page

    def _brand_changed(self, brand: str):
        model_combo = self.fields.get("model")
        if not model_combo:
            return
        previous = model_combo.currentText()
        model_combo.blockSignals(True)
        model_combo.clear()
        model_combo.addItems(self.model_catalog.get(brand, []))
        model_combo.setCurrentText(previous if previous in self.model_catalog.get(brand, []) else "")
        model_combo.blockSignals(False)

    def _change_save_path(self):
        current = self.manifest.get("generation", {}).get("save_path", "")
        destination = QFileDialog.getExistingDirectory(self, "选择默认保存文件夹", current or str(Path.home()))
        if destination:
            self.manifest = self.store.set_save_path(self.case_dir, destination)
            self._update_save_path_label()

    def _update_save_path_label(self):
        destination = self.manifest.get("generation", {}).get("save_path", "")
        if hasattr(self, "save_path_label"):
            self.save_path_label.setText(f"默认保存位置：{destination or '尚未设置，首次保存时选择'}")

    def _load_manifest(self):
        self.manifest = self.store.load(self.case_dir)
        self.case_label.setText(self.manifest["title"].upper())
        for key, card in self.slot_cards.items():
            card.set_image(self.store.asset_path(self.case_dir, key))
        for key, combo in self.fields.items():
            combo.blockSignals(True)
            combo.setCurrentText(self.manifest["information"].get(key, ""))
            combo.blockSignals(False)
        self._brand_changed(self.fields["brand"].currentText())
        self.plan_editor.blockSignals(True)
        self.plan_editor.setPlainText(self.manifest["ai_plan"].get("content", ""))
        self.plan_editor.blockSignals(False)
        self.confirm_plan.setChecked(self.manifest["ai_plan"].get("confirmed", False))
        self.use_ai.blockSignals(True)
        self.use_ai.setChecked(bool(self.manifest.get("use_ai", False)))
        self.use_ai.blockSignals(False)
        self._ai_mode_changed(self.use_ai.isChecked())
        self._show_previews()
        self._update_save_path_label()

    def _set_asset(self, slot: str, source: Path):
        try:
            self.store.set_asset(self.case_dir, slot, source)
            self.slot_cards[slot].set_image(self.store.asset_path(self.case_dir, slot))
        except ValueError as error:
            QMessageBox.warning(self, "无法使用图片", str(error))

    def _save_information(self):
        values = {key: combo.currentText() for key, combo in self.fields.items()}
        self.store.set_information(self.case_dir, values)

    def _plan_changed(self):
        self.store.set_ai_plan(self.case_dir, self.plan_editor.toPlainText(), self.confirm_plan.isChecked())

    def _ai_mode_changed(self, enabled: bool):
        manifest = self.store.load(self.case_dir)
        manifest["use_ai"] = bool(enabled)
        self.store.save(self.case_dir, manifest)
        self.ai_mode_label.setText(
            "当前：生成时会先使用 AI 方案" if enabled else "当前：跳过 AI，直接使用案例信息和素材生成"
        )
        for widget in (self.ai_checks, self.analyze_button, self.plan_editor, self.confirm_plan):
            if isinstance(widget, dict):
                for child in widget.values():
                    child.setEnabled(enabled)
            else:
                widget.setEnabled(enabled)

    def _analyze(self):
        selected = [self.store.asset_path(self.case_dir, key) for key, check in self.ai_checks.items() if check.isChecked()]
        selected = [path for path in selected if path]
        if not selected:
            QMessageBox.warning(self, "缺少案例图片", "至少选择 1 张案例图片后才能进行 AI 分析。")
            return
        self._save_information()
        self.analyze_button.setEnabled(False)
        try:
            settings = QSettings("Deaton Auto", "Image Case Studio")
            api_key = settings.value("openai/api_key", "", str).strip()
            model = settings.value("openai/model", "gpt-4.1-mini", str).strip()
            memory = ProjectMemory(self.store.projects_dir)
            plan = OpenAIPlanService(api_key=api_key or None, model=model or None).analyze(
                self.store.load(self.case_dir)["information"], selected,
                self.store.asset_path(self.case_dir, "logo"), memory.context()
            )
            self.plan_editor.setPlainText(plan)
            memory.record(f"AI方案已生成：本次使用 {len(selected)} 张案例图和 Logo；最终仍生成五张图，要求三种不同构图、Logo纯净区、无步骤编号、原图居中不裁切。")
            self.confirm_plan.setChecked(False)
        except Exception as error:
            QMessageBox.warning(self, "AI 分析未完成", str(error))
        finally:
            self.analyze_button.setEnabled(True)

    def _generate(self):
        self._save_information()
        self._plan_changed()
        manifest = self.store.load(self.case_dir)
        if manifest.get("use_ai", False) and (
            not manifest["ai_plan"].get("content", "").strip()
            or not manifest["ai_plan"].get("confirmed", False)
        ):
            QMessageBox.warning(self, "请先确认 AI 方案", "请先完成 AI 分析（或填写方案）并勾选“确认使用这份方案进行生成”。方案会先保存到本地，再由代码生成图片。")
            return
        self.generate_button.setEnabled(False)
        try:
            self.generator.generate(self.case_dir)
            self._show_previews()
        except Exception as error:
            QMessageBox.critical(self, "本地生成失败", str(error))
        finally:
            self.generate_button.setEnabled(True)

    def _show_previews(self):
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        paths = [Path(path) for path in self.manifest.get("generation", {}).get("preview_files", [])]
        try:
            paths = [Path(path) for path in self.store.load(self.case_dir)["generation"].get("preview_files", [])]
        except FileNotFoundError:
            return
        for index, path in enumerate(paths):
            if path.is_file():
                label = QLabel()
                label.setPixmap(QPixmap(str(path)).scaledToWidth(210, Qt.SmoothTransformation))
                label.setToolTip(path.name)
                self.preview_layout.addWidget(label, index // 3, index % 3)

    def _save_output(self):
        destination = self.manifest.get("generation", {}).get("save_path", "")
        if not destination:
            destination = QFileDialog.getExistingDirectory(self, "选择保存成品的文件夹")
            if not destination:
                return
            self.manifest = self.store.set_save_path(self.case_dir, destination)
        copied = self.generator.copy_to(self.case_dir, destination)
        if copied:
            QMessageBox.information(self, "已保存", f"已保存 {len(copied)} 张图片到\n{destination}")
        else:
            QMessageBox.warning(self, "没有可保存的图片", "请先生成预览。")

    def _update_step(self, index: int):
        titles = ("素材", "案例信息", "人工智能方案", "生成与保存")
        self.page_title.setText(titles[index])
        self.step_group.button(index).setChecked(True)


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.store = CaseStore()
        self.setWindowTitle("Deaton Auto · Image Case Studio")
        self.resize(1280, 820)
        self.setStyleSheet(STYLE)
        self.open_case(self.store.create("新案例"))

    def open_api_settings(self):
        settings = QSettings("Deaton Auto", "Image Case Studio")
        dialog = QDialog(self)
        dialog.setWindowTitle("OpenAI API 配置")
        dialog.setMinimumWidth(520)
        layout = QVBoxLayout(dialog)
        note = QLabel("API Key 仅保存在本机应用设置中，不会写入案例文件或提交到 GitHub。")
        note.setWordWrap(True)
        note.setObjectName("subtitle")
        layout.addWidget(note)
        form = QFormLayout()
        key_edit = QLineEdit()
        key_edit.setEchoMode(QLineEdit.Password)
        key_edit.setPlaceholderText("sk-...")
        key_edit.setText(settings.value("openai/api_key", "", str))
        model_edit = QLineEdit(settings.value("openai/model", "gpt-4.1-mini", str))
        model_edit.setPlaceholderText("gpt-4.1-mini")
        form.addRow("OpenAI API Key", key_edit)
        form.addRow("模型", model_edit)
        layout.addLayout(form)
        status = QLabel()
        status.setObjectName("subtitle")
        def update_status():
            status.setText("当前状态：已配置" if key_edit.text().strip() else "当前状态：未配置")
        key_edit.textChanged.connect(update_status)
        update_status()
        layout.addWidget(status)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        clear_button = buttons.addButton("清除 Key", QDialogButtonBox.DestructiveRole)
        clear_button.clicked.connect(lambda: key_edit.clear())
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            settings.setValue("openai/api_key", key_edit.text().strip())
            settings.setValue("openai/model", model_edit.text().strip() or "gpt-4.1-mini")
            QMessageBox.information(self, "已保存", "OpenAI API 配置已保存到本机。")

    def open_case(self, case_dir: Path):
        try:
            page = WorkbenchPage(self.store, case_dir)
            self.setCentralWidget(page)
            api_button = QPushButton("API 配置")
            api_button.setObjectName("secondary")
            api_button.clicked.connect(self.open_api_settings)
            page.findChild(QFrame, "panel").layout().addWidget(api_button)
        except (FileNotFoundError, ValueError) as error:
            QMessageBox.warning(self, "无法打开案例", str(error))


def main() -> int:
    """启动工作台；兼容直接运行 workbench 模块的方式。"""
    import sys

    from PySide6.QtWidgets import QApplication

    application = QApplication(sys.argv)
    application.setApplicationName("Deaton Auto Image Case Studio")
    window = ApplicationWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
