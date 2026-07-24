from __future__ import annotations

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1920, 1080
NAVY = "#0B1B2B"
BLUE = "#2B8CFF"
CYAN = "#5BD6FF"
WHITE = "#F8FBFF"
MUTED = "#A9B8C7"
LINE = "#29465F"

def font(size, bold=False):
    names = [
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()

def val(data, *keys):
    for key in keys:
        value = str(data.get(key, "") or "").strip()
        if value:
            return value.split("/", 1)[0].strip()
    return ""

def photo(path, size):
    if path and Path(path).is_file():
        with Image.open(path) as im:
            return ImageOps.contain(ImageOps.exif_transpose(im).convert("RGB"), size, Image.Resampling.LANCZOS)
    return Image.new("RGB", size, "#D9E1E8")

def logo(path):
    if not path or not Path(path).is_file():
        return None
    with Image.open(path) as im:
        out = im.convert("RGBA")
        # The supplied master has a white rectangular background. Make only
        # the near-white outside area transparent; the logo artwork itself
        # remains unchanged.
        pixels = out.load()
        for yy in range(out.height):
            for xx in range(out.width):
                r, g, b, a = pixels[xx, yy]
                if r > 242 and g > 242 and b > 242:
                    pixels[xx, yy] = (r, g, b, 0)
        out.thumbnail((210, 72), Image.Resampling.LANCZOS)
        return out

def draw_logo(canvas, path):
    mark = logo(path)
    if mark:
        canvas.alpha_composite(mark, (72, 52))

def fit_text(draw, value, max_width, start=78, minimum=34, bold=True):
    size = start
    while size > minimum and draw.textbbox((0, 0), value, font=font(size, bold))[2] > max_width:
        size -= 2
    return font(size, bold)

def text_block(draw, x, y, label, value, max_width, accent=BLUE, size=42):
    if not value:
        return y
    draw.text((x, y), label.upper(), font=font(19, True), fill=accent)
    f = fit_text(draw, value.upper(), max_width, size, 30, True)
    draw.text((x, y + 28), value.upper(), font=f, fill=WHITE)
    return y + f.size + 58

def base(data, assets, title, subtitle):
    canvas = Image.new("RGBA", (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)
    draw_logo(canvas, assets.get("logo", ""))
    draw.text((72, 160), title, font=font(22, True), fill=CYAN)
    draw.text((72, 202), subtitle, font=fit_text(draw, subtitle, 820, 84, 46), fill=WHITE)
    draw.line((72, 312, 840, 312), fill=LINE, width=3)
    return canvas

def page(data, assets, slot, title, subtitle, fields, accent_side=False):
    canvas = base(data, assets, title, subtitle)
    draw = ImageDraw.Draw(canvas)
    x_photo, y_photo, pw, ph = 980, 72, 860, 936
    im = photo(assets.get(slot, ""), (pw, ph))
    # photo is inset rather than dominant; keep real content visible without cropping
    canvas.alpha_composite(im.convert("RGBA"), (x_photo + (pw-im.width)//2, y_photo + (ph-im.height)//2))
    draw.rectangle((x_photo, y_photo, x_photo+pw, y_photo+ph), outline=LINE, width=3)
    y = 385
    for label, keys in fields:
        y = text_block(draw, 72, y, label, val(data, *keys), 800)
        if y > 930:
            break
    draw.text((72, 1000), "REMOTE AUTOMOTIVE ENGINEERING", font=font(17, True), fill=MUTED)
    return canvas

def generate(parameters: Path):
    payload = json.loads(parameters.read_text(encoding="utf-8"))
    data, assets = payload["information"], payload["assets"]
    out = Path(payload["case_dir"]) / "output-horizontal"
    out.mkdir(parents=True, exist_ok=True)
    pages = [
        ("01_overview_horizontal.png", page(data, assets, "vehicle", "CASE OVERVIEW", f"{val(data,'brand')} {val(data,'model')}".strip(), [("SERVICE", ("service","service_performed")), ("LOCATION", ("location","region")), ("RESULT", ("result","final_result"))])),
        ("02_fault_horizontal.png", page(data, assets, "fault", "CUSTOMER ISSUE", "WHAT NEEDED TO BE SOLVED", [("CUSTOMER REQUEST", ("customer_issue","customer_request","original_problem")), ("FAULT TYPE", ("fault_category",)), ("VEHICLE", ("brand","model"))])),
        ("03_diagnosis_horizontal.png", page(data, assets, "diagnosis", "DIAGNOSIS", "FINDING THE ROOT CAUSE", [("DIAGNOSTIC FINDING", ("diagnosis","diagnostic_finding")), ("FAULT CODES / SYMPTOMS", ("dtc_codes",)), ("EQUIPMENT", ("equipment",))])),
        ("04_programming_horizontal.png", page(data, assets, "programming", "REMOTE PROGRAMMING", "CODING AND MODULE ADAPTATION", [("SERVICE COMPLETED", ("service","service_performed")), ("PROGRAMMING WORK", ("programming",)), ("PROCESS", ("programming_detail",))])),
        ("05_result_horizontal.png", page(data, assets, "result", "COMPLETED", "REPAIR VERIFIED", [("FINAL RESULT", ("result","final_result")), ("VERIFICATION", ("verification",)), ("CONTACT", ("contact",)), ("WEBSITE", ("website",))])),
    ]
    paths=[]
    for name, im in pages:
        path=out/name
        im.convert("RGB").save(path, "PNG", optimize=True)
        paths.append(path.resolve())
    return paths

if __name__ == "__main__":
    print(json.dumps({"files": [str(p) for p in generate(Path(sys.argv[1]))]}))
