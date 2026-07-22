import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps

from engine.brand_service import BrandService
from engine.case_service import CaseService


TEMPLATES = {
    "case_cover": {
        "id": "case_cover",
        "name": "案例封面",
        "description": "品牌案例首图",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    },
    "diagnosis_summary": {
        "id": "diagnosis_summary",
        "name": "诊断摘要",
        "description": "故障与诊断过程展示图",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    },
    "result_card": {
        "id": "result_card",
        "name": "完成结果",
        "description": "维修完成发布图",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    },
}


@dataclass
class RenderResult:
    success: bool
    output_path: str = ""
    error: str = ""
    template_id: str = ""


class ImageCaseRenderer:
    """Renders reusable publication templates and records reproducible exports."""

    def __init__(self, project_path, brand_service=None):
        self.project_path = project_path
        self.case_service = CaseService(project_path)
        self.brand_service = brand_service or BrandService()

    def list_templates(self):
        return list(TEMPLATES.values())

    def render(self, template_id, asset_id=None):
        template = TEMPLATES.get(template_id)
        if template is None:
            return RenderResult(False, error="未找到图片模板", template_id=template_id)

        asset = self._resolve_asset(asset_id, template["required_category"])
        if asset is None:
            return RenderResult(
                False,
                error="请先导入车辆外观素材",
                template_id=template_id,
            )

        source_path = os.path.join(self.project_path, asset["path"])
        if not os.path.isfile(source_path):
            return RenderResult(False, error="素材文件不存在", template_id=template_id)

        brand = self.brand_service.load_profile()
        try:
            image = self._render_template(
                template_id,
                source_path,
                self.case_service.load_case_info(),
                brand,
                template["size"],
            )
        except OSError:
            return RenderResult(False, error="无法读取所选素材", template_id=template_id)

        output_dir = os.path.join(self.project_path, "output", "images")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        output_path = os.path.join(output_dir, filename)
        image.save(output_path, "JPEG", quality=92, optimize=True)

        self.case_service.record_export(
            {
                "id": uuid.uuid4().hex,
                "template_id": template_id,
                "asset_id": asset["id"],
                "path": os.path.relpath(output_path, self.project_path),
                "brand": brand.copy(),
                "created": datetime.now().isoformat(),
            }
        )
        return RenderResult(True, output_path=output_path, template_id=template_id)

    def render_all(self, asset_id=None):
        return [self.render(template_id, asset_id) for template_id in TEMPLATES]

    def _resolve_asset(self, asset_id, required_category):
        if asset_id:
            asset = self.case_service.get_asset(asset_id)
            if asset is None or asset.get("category") != required_category:
                return None
            return asset

        assets = self.case_service.list_assets(required_category)
        return next((asset for asset in assets if asset.get("is_primary")), assets[0] if assets else None)

    def _render_template(self, template_id, source_path, case_info, brand, size):
        if template_id == "case_cover":
            return self._render_cover(source_path, case_info, brand, size)
        if template_id == "diagnosis_summary":
            return self._render_diagnosis_summary(source_path, case_info, brand, size)
        return self._render_result_card(source_path, case_info, brand, size)

    def _render_cover(self, source_path, case_info, brand, size):
        canvas = Image.new("RGB", size, brand["primary_color"])
        source = Image.open(source_path).convert("RGB")
        hero = ImageOps.fit(source, (960, 720), method=Image.Resampling.LANCZOS)
        canvas.paste(hero, (60, 250))

        draw = ImageDraw.Draw(canvas)
        title_font = self._font(56)
        body_font = self._font(28)
        title, fault, result = self._case_text(case_info)
        draw.rectangle((0, 0, size[0], 190), fill=brand["primary_color"])
        draw.text((60, 48), self._safe_text(title.upper()), fill="#F8FAFC", font=title_font)
        draw.text((60, 128), self._safe_text(fault.upper()), fill=brand["accent_color"], font=body_font)
        draw.rectangle((60, 1010, 1020, 1014), fill=brand["accent_color"])
        draw.text((60, 1060), self._safe_text(brand["name"]), fill="#CBD5E1", font=body_font)
        if result:
            draw.text((60, 1110), self._safe_text(result), fill="#F8FAFC", font=body_font)
        return canvas

    def _render_diagnosis_summary(self, source_path, case_info, brand, size):
        canvas = Image.new("RGB", size, "#F8FAFC")
        source = Image.open(source_path).convert("RGB")
        hero = ImageOps.fit(source, (1080, 540), method=Image.Resampling.LANCZOS)
        canvas.paste(hero, (0, 0))

        draw = ImageDraw.Draw(canvas)
        title_font = self._font(50)
        section_font = self._font(30)
        body_font = self._font(26)
        title, fault, _ = self._case_text(case_info)
        draw.rectangle((0, 540, 1080, 1350), fill=brand["primary_color"])
        draw.rectangle((60, 620, 180, 628), fill=brand["accent_color"])
        draw.text((60, 670), self._safe_text(title), fill="#F8FAFC", font=title_font)
        draw.text((60, 770), "DIAGNOSIS", fill=brand["accent_color"], font=section_font)
        self._draw_wrapped(draw, fault, (60, 825), 960, body_font, "#E2E8F0")
        description = case_info.get("fault_description", "") or "基于案例素材完成故障诊断与处理。"
        self._draw_wrapped(draw, description, (60, 975), 960, body_font, "#E2E8F0")
        draw.text((60, 1220), self._safe_text(brand["name"]), fill="#94A3B8", font=section_font)
        return canvas

    def _render_result_card(self, source_path, case_info, brand, size):
        source = Image.open(source_path).convert("RGB")
        canvas = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", size, brand["primary_color"] + "CC")
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(canvas)
        title_font = self._font(56)
        body_font = self._font(30)
        _, _, result = self._case_text(case_info)
        draw.rectangle((60, 810, 1020, 1190), fill="#FFFFFF")
        draw.text((110, 875), "CASE COMPLETED", fill=brand["primary_color"], font=body_font)
        self._draw_wrapped(
            draw,
            result or "维修完成，车辆功能已验证。",
            (110, 945),
            840,
            title_font,
            brand["primary_color"],
        )
        draw.rectangle((60, 1230, 280, 1238), fill=brand["accent_color"])
        draw.text((60, 1265), self._safe_text(brand["name"]), fill="#F8FAFC", font=body_font)
        return canvas

    @staticmethod
    def _case_text(case_info):
        title = " ".join(
            value for value in (case_info.get("brand", ""), case_info.get("model", "")) if value
        ) or "AUTOMOTIVE CASE"
        fault = case_info.get("fault_category", "") or "PROGRAMMING CASE"
        return title, fault, case_info.get("repair_result", "")

    def _draw_wrapped(self, draw, text, position, max_width, font, fill):
        words = self._safe_text(text).split()
        if not words:
            return
        lines = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
        for index, line in enumerate(lines[:3]):
            draw.text((position[0], position[1] + index * (font.size + 12)), line, fill=fill, font=font)

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
