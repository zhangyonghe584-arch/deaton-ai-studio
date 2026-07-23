from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
INK = "#1E2329"
PAPER = "#F6F3ED"
MIST = "#E7E8E8"
ORANGE = "#D86F2A"
BLUE = "#123B68"
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def english(value, fallback="CASE UPDATE"):
    """Return safe English copy for generated images.

    Case files may be completed in Chinese. The UI can remain bilingual, but
    published artwork must never receive raw non-English case text.
    """
    value = str(value or "").strip()
    if not value or CJK.search(value):
        return fallback
    return value


def font(size: int, bold: bool = False):
    names = [
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def open_image(path: str, size: tuple[int, int], label: str) -> Image.Image:
    if path and Path(path).is_file():
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            return ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(0.5, 0.42))
    image = Image.new("RGB", size, MIST)
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, 14, size[0] - 14, size[1] - 14), outline="#B8BCBD", width=4)
    draw.text((size[0] // 2, size[1] // 2), label.upper(), font=font(25, True), fill="#7F868A", anchor="mm")
    return image


def logo_image(path: str) -> Image.Image | None:
    if not path or not Path(path).is_file():
        return None
    with Image.open(path) as image:
        result = ImageOps.exif_transpose(image).convert("RGBA")
        result.thumbnail((240, 110), Image.Resampling.LANCZOS)
        return result


def text(draw: ImageDraw.ImageDraw, position, value: str, size: int, color=INK, bold=False, anchor=None):
    draw.text(position, english(value).upper(), font=font(size, bold), fill=color, anchor=anchor)


def header(canvas: Image.Image, logo: Image.Image | None, page: str, index: int):
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 160), fill=PAPER)
    draw.rectangle((0, 154, W, 160), fill=ORANGE)
    if logo:
        canvas.alpha_composite(logo, (62, 30))
    # The top-left area is reserved for the supplied logo only.
    text(draw, (1016, 62), f"CASE {index:02d} / 05", 20, BLUE, True, "ra")
    text(draw, (1016, 96), page, 15, "#697176", True, "ra")


def footer(canvas: Image.Image):
    draw = ImageDraw.Draw(canvas)
    draw.line((64, 1816, 1016, 1816), fill="#C8CCCD", width=2)
    text(draw, (64, 1850), "DEATON AUTO · REMOTE PROGRAMMING", 16, "#697176", True)


def cover(data, assets, logo):
    photo = open_image(assets.get("vehicle", ""), (W, H), "Vehicle image").convert("RGBA")
    shade = Image.new("RGBA", (W, H), (10, 22, 36, 0))
    shade_draw = ImageDraw.Draw(shade)
    shade_draw.rectangle((0, 920, W, H), fill=(9, 23, 38, 220))
    canvas = Image.alpha_composite(photo, shade)
    header(canvas, logo, "CASE OVERVIEW", 1)
    draw = ImageDraw.Draw(canvas)
    text(draw, (64, 1045), "REMOTE PROGRAMMING CASE", 20, "#DDE8F3", True)
    text(draw, (64, 1100), english(data.get("brand"), "VEHICLE"), 36, PAPER, True)
    text(draw, (60, 1155), english(data.get("model"), "REMOTE SERVICE"), 78, PAPER, True)
    draw.rectangle((64, 1280, 510, 1287), fill=ORANGE)
    text(draw, (64, 1320), english(data.get("service"), "REMOTE PROGRAMMING"), 34, PAPER, True)
    text(draw, (64, 1382), f"{english(data.get('year'), 'VEHICLE')} · {english(data.get('fault_category'), 'TECHNICAL CASE')}", 23, "#DDE8F3")
    text(draw, (64, 1570), "RESULT", 17, "#B3C9DC", True)
    text(draw, (64, 1612), english(data.get("result"), "SERVICE COMPLETED"), 32, PAPER, True)
    return canvas


def detail_page(data, assets, logo, slot, title, section, index):
    canvas = Image.new("RGBA", (W, H), PAPER)
    header(canvas, logo, title, index)
    photo = open_image(assets.get(slot, ""), (952, 690), section)
    canvas.alpha_composite(photo.convert("RGBA"), (64, 220))
    draw = ImageDraw.Draw(canvas)
    text(draw, (64, 980), section, 18, ORANGE, True)
    text(draw, (64, 1030), title, 56, BLUE, True)
    draw.line((64, 1115, 1016, 1115), fill=ORANGE, width=5)
    if slot == "fault":
        values = [english(data.get("fault_category"), "REPORTED ISSUE"), english(data.get("model"), "VEHICLE"), english(data.get("year"), "CASE REVIEW")]
    elif slot == "diagnosis":
        values = ["Technical assessment", english(data.get("fault_category"), "SYSTEM FAULT"), "Verify before programming"]
    elif slot == "programming":
        values = [english(data.get("programming"), "MODULE CODING"), english(data.get("service"), "REMOTE PROGRAMMING"), "Controlled remote procedure"]
    else:
        values = [english(data.get("result"), "SERVICE COMPLETED"), "Function verified", "Case completed"]
    y = 1195
    for number, value in enumerate(values, 1):
        text(draw, (70, y), f"0{number}", 20, ORANGE, True)
        text(draw, (150, y), value, 30, INK, True)
        draw.line((64, y + 58, 1016, y + 58), fill="#D4D7D6", width=2)
        y += 126
    footer(canvas)
    return canvas


def generate(parameters: Path) -> list[Path]:
    payload = json.loads(parameters.read_text(encoding="utf-8"))
    case_dir = Path(payload["case_dir"])
    output_dir = case_dir / "output"
    output_dir.mkdir(exist_ok=True)
    data = dict(payload["information"])
    data["ai_plan"] = payload.get("ai_plan", {})
    assets = payload["assets"]
    logo = logo_image(assets.get("logo", ""))
    pages = [
        ("01_case_overview.png", cover(data, assets, logo)),
        ("02_vehicle_fault.png", detail_page(data, assets, logo, "fault", "VEHICLE FAULT", "REPORTED ISSUE", 2)),
        ("03_diagnosis.png", detail_page(data, assets, logo, "diagnosis", "DIAGNOSIS", "ANALYSIS", 3)),
        ("04_programming.png", detail_page(data, assets, logo, "programming", "PROGRAMMING", "REMOTE PROCEDURE", 4)),
        ("05_result.png", detail_page(data, assets, logo, "result", "COMPLETED", "FINAL RESULT", 5)),
    ]
    paths = []
    for filename, image in pages:
        path = output_dir / filename
        image.convert("RGB").save(path, "PNG", optimize=True)
        paths.append(path.resolve())
    return paths


if __name__ == "__main__":
    parameter_file = Path(sys.argv[1]).resolve()
    paths = generate(parameter_file)
    print(json.dumps({"files": [str(path) for path in paths], "generated_at": datetime.now(timezone.utc).isoformat()}))
