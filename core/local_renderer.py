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
STYLE = "editorial"

def palette():
    if STYLE == "dark":
        return {"paper": "#101820", "ink": "#F4F7F8", "blue": "#8FD3FF", "accent": "#FFB45C", "mist": "#27343D"}
    if STYLE == "contrast":
        return {"paper": "#FFFFFF", "ink": "#101820", "blue": "#0B4F71", "accent": "#E4572E", "mist": "#E9EEF0"}
    return {"paper": "#F5F1E9", "ink": "#17212B", "blue": "#164A67", "accent": "#C94F2D", "mist": "#E4E7E5"}


def english(value, fallback="CASE UPDATE"):
    """Return safe English copy for generated images.

    Case files may be completed in Chinese. The UI can remain bilingual, but
    published artwork must never receive raw non-English case text.
    """
    value = str(value or "").strip()
    if not value:
        return fallback
    # Bilingual UI values are stored as "English / 中文".  Published artwork
    # uses only the English side; custom Chinese-only input uses the fallback.
    if "/" in value:
        candidate = value.split("/", 1)[0].strip()
        if candidate and not CJK.search(candidate):
            return candidate
    if CJK.search(value):
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


def supplied(data, key: str) -> str:
    """Return a field only when the user supplied it; empty fields render nothing."""
    raw = str(data.get(key, "") or "").strip()
    return english(raw, "") if raw else ""


def draw_field_list(draw, data, fields, start_y, max_width=900):
    """Draw compact optional fields and return the next free y position."""
    y = start_y
    visible = [(label, supplied(data, key)) for key, label in fields]
    visible = [(label, value) for label, value in visible if value]
    if not visible:
        return y
    # More content gets a smaller type size and tighter spacing automatically.
    p = palette()
    value_size = 36 if len(visible) <= 3 else 31 if len(visible) <= 5 else 27
    for label, value in visible:
        lines = text_lines(value, font(value_size, True), max_width - 70)
        text(draw, (70, y), label, 18, p["accent"], True)
        for line in lines[:2]:
            text(draw, (70, y + 34), line, value_size, p["ink"], True)
            y += value_size + 8
        y += 24
    return y


def text_lines(value, typeface, width):
    words = value.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and typeface.getlength(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [value]


def header(canvas: Image.Image, logo: Image.Image | None):
    draw = ImageDraw.Draw(canvas)
    p = palette()
    draw.rectangle((0, 0, W, 178), fill=p["paper"])
    draw.rectangle((0, 170, W, 178), fill=p["accent"])
    if logo:
        canvas.alpha_composite(logo, (62, 30))
    # The header is intentionally logo-only. Do not add case IDs, page numbers,
    # STEP labels, or placeholder digits to published case artwork.


def footer(canvas: Image.Image):
    draw = ImageDraw.Draw(canvas)
    p = palette()
    draw.line((64, 1816, 1016, 1816), fill=p["mist"], width=2)
    text(draw, (64, 1850), "DEATON AUTO · REMOTE PROGRAMMING", 16, "#697176", True)


def cover(data, assets, logo):
    p = palette()
    photo = open_image(assets.get("vehicle", ""), (W, H), "Vehicle image").convert("RGBA")
    shade = Image.new("RGBA", (W, H), (10, 22, 36, 0))
    shade_draw = ImageDraw.Draw(shade)
    shade_draw.rectangle((0, 880, W, H), fill=(9, 23, 38, 230))
    canvas = Image.alpha_composite(photo, shade)
    header(canvas, logo)
    draw = ImageDraw.Draw(canvas)
    text(draw, (64, 1015), "REMOTE PROGRAMMING CASE", 25, p["accent"], True)
    brand = supplied(data, "brand") or "VEHICLE"
    model = supplied(data, "model") or "REMOTE SERVICE"
    text(draw, (64, 1100), brand, 36, PAPER, True)
    text(draw, (60, 1125), model, 96, PAPER, True)
    draw.rectangle((64, 1270, 720, 1282), fill=p["accent"])
    y = 1325
    y = draw_field_list(draw, data, [("service", "SERVICE"), ("year", "YEAR"), ("mileage", "MILEAGE"), ("location", "LOCATION")], y, 900)
    if supplied(data, "result"):
        text(draw, (64, min(y + 35, 1570)), "RESULT", 17, "#B3C9DC", True)
        text(draw, (64, min(y + 77, 1612)), supplied(data, "result"), 32, PAPER, True)
    return canvas


def detail_page(data, assets, logo, slot, title, section):
    p = palette()
    canvas = Image.new("RGBA", (W, H), p["paper"])
    header(canvas, logo)
    photo = open_image(assets.get(slot, ""), (952, 690), section)
    canvas.alpha_composite(photo.convert("RGBA"), (64, 220))
    draw = ImageDraw.Draw(canvas)
    text(draw, (64, 980), section, 24, p["accent"], True)
    text(draw, (64, 1025), title, 72, p["blue"], True)
    draw.line((64, 1125, 1016, 1125), fill=p["accent"], width=8)
    field_map = {
        "fault": [("customer_issue", "CUSTOMER ISSUE"), ("fault_category", "FAULT CATEGORY"), ("dtc_codes", "FAULT CODES / SYMPTOMS"), ("model", "VEHICLE")],
        "diagnosis": [("diagnosis", "DIAGNOSTIC FINDING"), ("fault_category", "FAULT CATEGORY"), ("equipment", "DIAGNOSTIC EQUIPMENT")],
        "programming": [("service", "SERVICE COMPLETED"), ("programming", "PROGRAMMING WORK"), ("programming_detail", "PROCESS")],
        "result": [("result", "RESULT"), ("final_status", "FINAL STATUS"), ("verification", "VERIFICATION"), ("contact", "CONTACT"), ("website", "WEBSITE")],
    }
    draw_field_list(draw, data, field_map.get(slot, []), 1205, 900)
    footer(canvas)
    return canvas


def generate(parameters: Path) -> list[Path]:
    global STYLE
    payload = json.loads(parameters.read_text(encoding="utf-8"))
    case_dir = Path(payload["case_dir"])
    output_dir = case_dir / "output"
    output_dir.mkdir(exist_ok=True)
    STYLE = str(payload.get("style", "editorial"))
    data = dict(payload["information"])
    data["ai_plan"] = payload.get("ai_plan", {})
    assets = payload["assets"]
    logo = logo_image(assets.get("logo", ""))
    pages = [
        ("01_case_overview.png", cover(data, assets, logo)),
        ("02_vehicle_fault.png", detail_page(data, assets, logo, "fault", "VEHICLE FAULT", "REPORTED ISSUE")),
        ("03_diagnosis.png", detail_page(data, assets, logo, "diagnosis", "DIAGNOSIS", "ANALYSIS")),
        ("04_programming.png", detail_page(data, assets, logo, "programming", "PROGRAMMING", "REMOTE PROCEDURE")),
        ("05_result.png", detail_page(data, assets, logo, "result", "COMPLETED", "FINAL RESULT")),
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
