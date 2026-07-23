from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
PAPER = "#F6F3ED"
INK = "#1E2329"
BLUE = "#123B68"
ORANGE = "#D86F2A"
MIST = "#E7E8E8"


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


def fit(path: str, size: tuple[int, int], label: str, centering=(0.5, 0.5)):
    if path and Path(path).is_file():
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            return ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=centering)
    image = Image.new("RGB", size, MIST)
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, size[0] - 12, size[1] - 12), outline="#B8BCBD", width=4)
    draw.text((size[0] // 2, size[1] // 2), label.upper(), font=font(24, True), fill="#7F868A", anchor="mm")
    return image


def logo(path: str):
    if not path or not Path(path).is_file():
        return None
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")
        image.thumbnail((210, 92), Image.Resampling.LANCZOS)
        return image


def txt(draw, xy, value, size, color=INK, bold=False, anchor=None):
    draw.text(xy, (value or "—").upper(), font=font(size, bold), fill=color, anchor=anchor)


def frame(data, assets, logo_img, slot, title, section, index, style):
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    accent = [ORANGE, BLUE, "#6C7C56"][style]
    if style == 0:
        draw.rectangle((0, 0, W, 145), fill=BLUE)
        txt(draw, (62, 50), "DEATON AUTO", 28, PAPER, True)
        txt(draw, (1018, 52), f"{index:02d} / 05", 18, PAPER, True, "ra")
    elif style == 1:
        draw.rectangle((0, 0, W, 12), fill=accent)
        txt(draw, (64, 64), f"DEATON AUTO  /  {section}", 19, BLUE, True)
        txt(draw, (1018, 64), f"{index:02d}", 22, accent, True, "ra")
    else:
        draw.rectangle((0, 0, W, 155), fill="#FFFFFF")
        draw.line((64, 145, 1016, 145), fill=accent, width=5)
        txt(draw, (64, 54), "DEATON AUTO", 28, BLUE, True)
        txt(draw, (1018, 56), f"CASE {index:02d}", 17, "#697176", True, "ra")
    if logo_img:
        canvas.paste(logo_img, (62, 24 if style != 1 else 24), logo_img)
    if slot == "fault":
        photo_size = (690, 920)
        photo_position = (195, 190 if style != 2 else 205)
        y = 1190 if style != 2 else 1215
    else:
        photo_size = (952, 690)
        photo_position = (64, 205 if style != 2 else 220)
        y = 965 if style != 2 else 990
    photo = fit(assets.get(slot, ""), photo_size, section, (0.5, 0.42))
    canvas.paste(photo, photo_position)
    txt(draw, (64, y), section, 17, accent, True)
    txt(draw, (64, y + 55), title, 52 if style != 1 else 46, BLUE, True)
    draw.line((64, y + 135, 1016, y + 135), fill=accent, width=5)
    values = {
        "fault": [data.get("fault_category", ""), data.get("model", ""), data.get("year", "")],
        "diagnosis": ["Technical assessment", data.get("fault_category", ""), "Verify before programming"],
        "programming": [data.get("programming", ""), data.get("service", ""), "Controlled remote procedure"],
        "result": [data.get("result", ""), "Function verified", "Case completed"],
    }.get(slot, [data.get("service", ""), data.get("region", ""), data.get("result", "")])
    for number, value in enumerate(values, 1):
        yy = y + 215 + (number - 1) * 126
        txt(draw, (70, yy), f"0{number}", 19, accent, True)
        txt(draw, (150, yy), value, 28 if style != 1 else 25, INK, True)
        draw.line((64, yy + 55, 1016, yy + 55), fill="#D4D7D6", width=2)
    txt(draw, (64, 1850), "DEATON AUTO · REMOTE PROGRAMMING", 15, "#697176", True)
    return canvas


def cover(data, assets, logo_img, style):
    accent = [ORANGE, BLUE, "#6C7C56"][style]
    photo = fit(assets.get("vehicle", ""), (W, H), "Vehicle image", (0.5, 0.42))
    canvas = photo.copy()
    draw = ImageDraw.Draw(canvas)
    overlay = Image.new("RGBA", (W, H), (7, 22, 36, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 850, W, H), fill=(7, 22, 36, 225 if style != 2 else 205))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    if style == 0:
        draw.rectangle((0, 0, W, 150), fill=BLUE)
    elif style == 1:
        draw.rectangle((0, 0, 22, H), fill=accent)
        draw.rectangle((22, 0, W, 130), fill="#FFFFFF")
    else:
        draw.rectangle((0, 0, W, 130), fill="#FFFFFF")
        draw.line((64, 120, 1016, 120), fill=accent, width=5)
    if logo_img:
        canvas.paste(logo_img, (62, 25), logo_img)
    else:
        txt(draw, (64, 52), "DEATON AUTO", 30, PAPER if style == 0 else BLUE, True)
    txt(draw, (1018, 55), "01 / 05", 18, PAPER if style == 0 else BLUE, True, "ra")
    txt(draw, (64, 1030), "REMOTE PROGRAMMING CASE", 19, "#DDE8F3", True)
    txt(draw, (64, 1090), data.get("brand", ""), 34, PAPER, True)
    txt(draw, (60, 1148), data.get("model", ""), 72, PAPER, True)
    draw.rectangle((64, 1270, 510, 1277), fill=accent)
    txt(draw, (64, 1310), data.get("service", ""), 31, PAPER, True)
    txt(draw, (64, 1370), f"{data.get('year', '')} · {data.get('fault_category', '')}", 22, "#DDE8F3")
    txt(draw, (64, 1560), "RESULT", 16, "#B3C9DC", True)
    txt(draw, (64, 1600), data.get("result", ""), 30, PAPER, True)
    return canvas


def generate(parameters: Path) -> list[Path]:
    payload = json.loads(parameters.read_text(encoding="utf-8"))
    case_dir = Path(payload["case_dir"])
    output_dir = case_dir / "output"
    output_dir.mkdir(exist_ok=True)
    data = dict(payload["information"])
    assets = payload["assets"]
    logo_img = logo(assets.get("logo", ""))
    pages = [("01_vehicle_exterior", "vehicle", "VEHICLE EXTERIOR", "VEHICLE", "Vehicle Exterior"),
             ("02_dashboard_fault", "fault", "DASHBOARD & FAULT", "FAULT", "Dashboard / Fault"),
             ("03_diagnosis", "diagnosis", "DIAGNOSIS", "ANALYSIS", "Diagnosis"),
             ("04_programming", "programming", "PROGRAMMING", "REMOTE PROCEDURE", "Programming"),
             ("05_repair_completed", "result", "REPAIR COMPLETED", "FINAL RESULT", "Repair Completed")]
    paths = []
    for style in range(3):
        template_dir = output_dir / f"template_{style + 1}"
        template_dir.mkdir(exist_ok=True)
        for number, (stem, slot, title, section, label) in enumerate(pages, 1):
            image = cover(data, assets, logo_img, style) if number == 1 else frame(data, assets, logo_img, slot, title, section, number, style)
            path = template_dir / f"{number:02d}_{stem}.png"
            image.save(path, "PNG", optimize=True)
            paths.append(path.resolve())
    return paths


if __name__ == "__main__":
    paths = generate(Path(sys.argv[1]).resolve())
    print(json.dumps({"files": [str(path) for path in paths], "generated_at": datetime.now(timezone.utc).isoformat()}))
