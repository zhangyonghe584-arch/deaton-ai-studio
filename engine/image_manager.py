import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime

from PIL import Image

from engine.case_service import CaseService


CATEGORY_MAP = {
    "01 车辆外观": "01_vehicle",
    "02 故障现象": "02_fault",
    "03 诊断过程": "03_diagnosis",
    "04 编程过程": "04_programming",
    "05 完成结果": "05_result",
    "06 技术资料": "06_technical"
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass
class ImageImportResult:
    success: bool
    target_path: str = ""
    asset: dict = None
    error: str = ""


class ImageManager:
    """Imports images into the existing six-category project structure."""

    def __init__(self, project_path):
        self.project_path = project_path
        self.case_service = CaseService(project_path)

    def save_image(self, image_path, category_name):
        """Compatibility wrapper for the original image import API."""
        result = self.import_image(image_path, category_name)
        return result.target_path if result.success else None

    def import_image(self, image_path, category_name):
        if category_name not in CATEGORY_MAP:
            return ImageImportResult(False, error="未知的素材分类")
        if not os.path.isfile(image_path):
            return ImageImportResult(False, error="图片文件不存在")

        extension = os.path.splitext(image_path)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return ImageImportResult(False, error="不支持的图片格式")

        try:
            with Image.open(image_path) as image:
                image.verify()
        except (OSError, ValueError):
            return ImageImportResult(False, error="无法读取图片文件")

        asset_id = uuid.uuid4().hex
        folder = CATEGORY_MAP[category_name]
        target_dir = os.path.join(self.project_path, "images", folder)
        os.makedirs(target_dir, exist_ok=True)
        target_filename = f"{asset_id}{extension}"
        target_path = os.path.join(target_dir, target_filename)

        try:
            shutil.copy2(image_path, target_path)
        except OSError:
            return ImageImportResult(False, error="复制图片到项目失败")

        asset = {
            "id": asset_id,
            "category": category_name,
            "path": os.path.relpath(target_path, self.project_path),
            "original_filename": os.path.basename(image_path),
            "created": datetime.now().isoformat(),
        }
        try:
            self.case_service.add_asset(asset)
        except OSError:
            if os.path.exists(target_path):
                os.unlink(target_path)
            return ImageImportResult(False, error="保存素材记录失败")

        return ImageImportResult(True, target_path=target_path, asset=asset)
