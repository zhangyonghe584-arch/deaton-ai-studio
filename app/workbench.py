from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QStringListModel
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
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
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.ai_plan import OpenAIPlanService
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
        instruction = QLabel("固定六槽位，每格至多一张图片。空槽位不阻止生成；将新图拖入原格即可更新。")
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
        note = QLabel("所有字段都可留空或直接输入。可扩展选项保存在 config/options.json。")
        note.setObjectName("subtitle")
        card = QFrame(objectName="panel")
        form = QFormLayout(card)
        form.setContentsMargins(28, 28, 28, 28)
        options = self.store.options()
        self.model_catalog = self.store.model_options()
        for key, label in CASE_FIELDS:
            combo = QComboBox(editable=True)
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
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _ai_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        warning = QLabel("仅在点击“分析所选素材”时调用 OpenAI。最多 3 张由你勾选的图片会被压缩后上传；不会扫描全部素材。")
        warning.setObjectName("subtitle")
        layout.addWidget(warning)
        selector = QFrame(objectName="panel")
        selector_layout = QVBoxLayout(selector)
        selector_layout.setContentsMargins(20, 20, 20, 20)
        selector_layout.addWidget(QLabel("选择用于分析的素材（最多 3 张）"))
        self.ai_checks: dict[str, QCheckBox] = {}
        for key, label in SLOT_SPECS:
            if key != "logo":
                check = QCheckBox(label)
                self.ai_checks[key] = check
                selector_layout.addWidget(check)
        self.analyze_button = QPushButton("分析所选素材")
        self.analyze_button.clicked.connect(self._analyze)
        selector_layout.addWidget(self.analyze_button)
        self.plan_editor = QPlainTextEdit(placeholderText="分析方案会显示在这里。你可以自行修改，再确认用于本地生成。")
        self.plan_editor.textChanged.connect(self._plan_changed)
        self.confirm_plan = QCheckBox("确认使用这份方案进行生成")
        self.confirm_plan.toggled.connect(self._plan_changed)
        layout.addWidget(selector)
        layout.addSpacing(12)
        layout.addWidget(QLabel("可编辑方案", objectName="title"))
        layout.addWidget(self.plan_editor, 1)
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

    def _analyze(self):
        selected = [self.store.asset_path(self.case_dir, key) for key, check in self.ai_checks.items() if check.isChecked()]
        selected = [path for path in selected if path]
        if len(selected) > OpenAIPlanService.max_images:
            QMessageBox.warning(self, "最多三张图片", "请只选择最多三张素材进行分析。")
            return
        self._save_information()
        self.analyze_button.setEnabled(False)
        try:
            plan = OpenAIPlanService().analyze(self.store.load(self.case_dir)["information"], selected)
            self.plan_editor.setPlainText(plan)
            self.confirm_plan.setChecked(False)
        except Exception as error:
            QMessageBox.warning(self, "AI 分析未完成", str(error))
        finally:
            self.analyze_button.setEnabled(True)

    def _generate(self):
        self._save_information()
        self._plan_changed()
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

    def open_case(self, case_dir: Path):
        try:
            self.setCentralWidget(WorkbenchPage(self.store, case_dir))
        except (FileNotFoundError, ValueError) as error:
            QMessageBox.warning(self, "无法打开案例", str(error))
