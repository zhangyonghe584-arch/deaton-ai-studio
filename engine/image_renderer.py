import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps

from engine.case_service import CaseService


TEMPLATES = {
    "case_cover": {
        "id": "case_cover",
        "name": "案例封面",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    }
}


@dataclass
class RenderResult:
    success: bool
    output_path: str = ""
    error: str = ""


class ImageCaseRenderer:
    """Renders fixed image-case templates and records reproducible exports."""

    def __init__(self, project_path):
        self.project_path = project_path
        self.case_service = CaseService(project_path)

    def list_templates(self):
        return list(TEMPLATES.values())

    def render(self, template_id, asset_id):
        template = TEMPLATES.get(template_id)
        if template is None:
            return RenderResult(False, error="未找到图片模板")

        asset = self.case_service.get_asset(asset_id)
        if asset is None:
            return RenderResult(False, error="未找到所选素材")
        if asset.get("category") != template["required_category"]:
            return RenderResult(False, error="封面模板需要使用车辆外观素材")

        source_path = os.path.join(self.project_path, asset["path"])
        if not os.path.isfile(source_path):
            return RenderResult(False, error="素材文件不存在")

        try:
            image = self._render_cover(source_path, self.case_service.load_case_info(), template["size"])
        except OSError:
            return RenderResult(False, error="无法读取所选素材")

        output_dir = os.path.join(self.project_path, "output", "images")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"case_cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        output_path = os.path.join(output_dir, filename)
        image.save(output_path, "JPEG", quality=92, optimize=True)

        self.case_service.record_export(
            {
                "id": uuid.uuid4().hex,
                "template_id": template_id,
                "asset_id": asset_id,
                "path": os.path.relpath(output_path, self.project_path),
                "created": datetime.now().isoformat(),
            }
        )
        return RenderResult(True, output_path=output_path)

    def _render_cover(self, source_path, case_info, size):
        canvas = Image.new("RGB", size, "#0B1220")
        source = Image.open(source_path).convert("RGB")
        hero = ImageOps.fit(source, (960, 720), method=Image.Resampling.LANCZOS)
        canvas.paste(hero, (60, 250))

        draw = ImageDraw.Draw(canvas)
        title_font = self._font(56)
        body_font = self._font(28)
        brand = " ".join(
            value for value in (case_info.get("brand", ""), case_info.get("model", "")) if value
        ) or "AUTOMOTIVE CASE"
        fault = case_info.get("fault_category", "PROGRAMMING CASE") or "PROGRAMMING CASE"
        result = case_info.get("repair_result", "")

        draw.rectangle((0, 0, size[0], 190), fill="#111D30")
        draw.text((60, 48), self._safe_text(brand.upper()), fill="#F8FAFC", font=title_font)
        draw.text((60, 128), self._safe_text(fault.upper()), fill="#67E8F9", font=body_font)
        draw.rectangle((60, 1010, 1020, 1014), fill="#22D3EE")
        draw.text((60, 1060), "DEATON AUTO", fill="#94A3B8", font=body_font)
        if result:
            draw.text((60, 1110), self._safe_text(result), fill="#F8FAFC", font=body_font)
        return canvas

    @staticmethod
    def _font(size):
        font_paths = (
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyh.ttc"),
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyhbd.ttc"),
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "DejaVuSans.ttf",
        )
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _safe_text(value):
        return str(value)
