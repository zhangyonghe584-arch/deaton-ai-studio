import os
import uuid
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
        "name": "诊断过程",
        "description": "故障诊断展示",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    },

    "result_card": {
        "id": "result_card",
        "name": "完成结果",
        "description": "维修完成展示",
        "size": (1080, 1350),
        "required_category": "01 车辆外观",
    },
}


class RenderResult:

    def __init__(
        self,
        success,
        output_path="",
        error="",
        template_id=""
    ):
        self.success = success
        self.output_path = output_path
        self.error = error
        self.template_id = template_id



class ImageCaseRenderer:


    def __init__(
        self,
        project_path,
        brand_service=None
    ):

        self.project_path = project_path

        self.case_service = CaseService(
            project_path
        )

        self.brand_service = (
    brand_service
    or BrandService(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
)


    def list_templates(self):

        return list(
            TEMPLATES.values()
        )


    def render(
        self,
        template_id,
        asset_id=None
    ):

        template = TEMPLATES.get(
            template_id
        )

        if not template:
            return RenderResult(
                False,
                error="模板不存在",
                template_id=template_id
            )


        asset = self._resolve_asset(
            asset_id,
            template["required_category"]
        )

        if not asset:
            return RenderResult(
                False,
                error="没有可用素材",
                template_id=template_id
            )


        source_path = os.path.join(
            self.project_path,
            asset["path"]
        )


        if not os.path.exists(source_path):

            return RenderResult(
                False,
                error="素材不存在",
                template_id=template_id
            )


        brand = self.brand_service.load_profile()


        case_info = (
            self.case_service
            .load_case_info()
        )


        image = self._render_template(
            template_id,
            source_path,
            case_info,
            brand,
            template["size"]
        )


        output_dir = os.path.join(
            self.project_path,
            "output",
            "images"
        )


        os.makedirs(
            output_dir,
            exist_ok=True
        )


        filename = (
            template_id
            + "_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + "_"
            + uuid.uuid4().hex[:8]
            + ".jpg"
        )


        output_path = os.path.join(
            output_dir,
            filename
        )


        image.save(
            output_path,
            "JPEG",
            quality=95
        )


        brand_snapshot = {
            "name": brand.get("name",""),
            "subtitle": brand.get("subtitle",""),
            "primary_color": brand.get("primary_color",""),
            "accent_color": brand.get("accent_color",""),
            "logo": brand.get("logo",""),
            "footer": brand.get("footer","")
        }


        self.case_service.record_export(
            {
                "id": uuid.uuid4().hex,
                "template_id": template_id,
                "asset_id": asset["id"],
                "path": os.path.relpath(
                    output_path,
                    self.project_path
                ),
                "brand": brand_snapshot,
                "created": datetime.now().isoformat()
            }
        )


        return RenderResult(
            True,
            output_path,
            template_id=template_id
        )



    def render_all(self, asset_id=None):

        return [
            self.render(
                template_id,
                asset_id
            )

            for template_id in TEMPLATES
        ]



    def _resolve_asset(
        self,
        asset_id,
        category
    ):

        if asset_id:

            asset = self.case_service.get_asset(
                asset_id
            )

            if asset and asset["category"] == category:
                return asset

            return None


        assets = self.case_service.list_assets(
            category
        )


        if not assets:
            return None


        return assets[0]



    def _render_template(
        self,
        template_id,
        source,
        case,
        brand,
        size
    ):


        if template_id == "case_cover":

            return self._cover(
                source,
                case,
                brand,
                size
            )


        if template_id == "diagnosis_summary":

            return self._diagnosis(
                source,
                case,
                brand,
                size
            )


        return self._result(
            source,
            case,
            brand,
            size
        )



    def _cover(
        self,
        source,
        case,
        brand,
        size
    ):


        canvas = Image.new(
            "RGB",
            size,
            brand["primary_color"]
        )


        car = Image.open(
            source
        ).convert("RGB")


        car = ImageOps.fit(
            car,
            (960,700)
        )


        canvas.paste(
            car,
            (60,260)
        )


        draw = ImageDraw.Draw(
            canvas
        )


        self._draw_logo(
            canvas,
            brand
        )


        title = (
            case.get("brand","")
            +
            " "
            +
            case.get("model","")
        )


        draw.text(
            (60,80),
            title.strip()
            or "AUTOMOTIVE CASE",
            font=self._font(55),
            fill="white"
        )


        draw.text(
            (60,160),
            case.get(
                "fault_category",
                "Remote Programming"
            ),
            font=self._font(30),
            fill=brand["accent_color"]
        )


        draw.text(
            (60,1080),
            brand["name"],
            font=self._font(32),
            fill="white"
        )


        return canvas



    def _diagnosis(
        self,
        source,
        case,
        brand,
        size
    ):


        canvas = Image.new(
            "RGB",
            size,
            "white"
        )


        img = Image.open(
            source
        ).convert("RGB")


        img = ImageOps.fit(
            img,
            (1080,600)
        )


        canvas.paste(
            img,
            (0,0)
        )


        draw = ImageDraw.Draw(
            canvas
        )


        draw.text(
            (60,700),
            "DIAGNOSTIC PROCESS",
            font=self._font(45),
            fill=brand["primary_color"]
        )


        draw.text(
            (60,800),
            case.get(
                "fault_description",
                ""
            ),
            font=self._font(30),
            fill="black"
        )


        return canvas



    def _result(
        self,
        source,
        case,
        brand,
        size
    ):


        canvas = ImageOps.fit(
            Image.open(source).convert("RGB"),
            size
        )


        draw = ImageDraw.Draw(
            canvas
        )


        draw.rectangle(
            (40,900,1040,1250),
            fill="white"
        )


        draw.text(
            (80,980),
            "COMPLETED",
            font=self._font(55),
            fill=brand["primary_color"]
        )


        draw.text(
            (80,1080),
            case.get(
                "repair_result",
                ""
            ),
            font=self._font(30),
            fill="black"
        )


        return canvas

    def _draw_logo(self, canvas, brand):

        logo_path = brand.get("logo", "")

        if not logo_path:
            return


        if not os.path.isabs(logo_path):

            logo_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                logo_path.replace("\\", os.sep)
            )


        if not os.path.exists(logo_path):

            print(
                "Logo不存在:",
                logo_path
            )

            return


        try:

            logo = Image.open(
                logo_path
            ).convert(
                "RGBA"
            )


            logo.thumbnail(
                (260,140)
            )


            canvas.paste(
                logo,
                (760,40),
                logo
            )


            print(
                "Logo显示成功:",
                logo_path
            )


        except Exception as error:

            print(
                "Logo错误:",
                error
            )



    def _font(self,size):

        paths = [

            r"C:\Windows\Fonts\msyh.ttc",

            r"C:\Windows\Fonts\msyhbd.ttc"

        ]


        for path in paths:

            if os.path.exists(path):

                return ImageFont.truetype(
                    path,
                    size
                )


        return ImageFont.load_default()