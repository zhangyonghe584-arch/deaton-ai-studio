from __future__ import annotations

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
NAVY, BLUE, CYAN, INK, PALE = '#081827', '#1769D5', '#35C6F4', '#11263A', '#EEF4F8'

def f(size, bold=False):
    names = [
        'C:/Windows/Fonts/seguisb.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for n in names:
        if Path(n).is_file(): return ImageFont.truetype(n, size)
    return ImageFont.load_default()

def value(d, *keys):
    for k in keys:
        v = str(d.get(k, '') or '').strip()
        if v: return v.split('/', 1)[0].strip()
    return ''

def image(path, size, cover=False):
    if not path or not Path(path).is_file(): return Image.new('RGB', size, '#D9E2EB')
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS) if cover else ImageOps.contain(im, size, method=Image.Resampling.LANCZOS)

def logo(path, max_size=(220, 74)):
    if not path or not Path(path).is_file(): return None
    with Image.open(path) as im: out = im.convert('RGBA')
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r,g,b,a = px[x,y]
            if r > 242 and g > 242 and b > 242: px[x,y] = (r,g,b,0)
    bbox = out.getbbox()
    if bbox: out = out.crop(bbox)
    out.thumbnail(max_size, Image.Resampling.LANCZOS)
    return out

def add_logo(c, path, x=64, y=44):
    m = logo(path)
    if m:
        # Keep the master artwork intact, but place it inside a restrained
        # brand capsule so it reads as part of the layout rather than a
        # floating image in the margin.
        m.thumbnail((150, 52), Image.Resampling.LANCZOS)
        ImageDraw.Draw(c).rounded_rectangle((x-16, y-10, x+m.width+22, y+m.height+10), radius=18, fill='white')
        c.alpha_composite(m, (x, y))

def wrap(draw, text, font, width):
    words = str(text).split(); lines=[]; line=''
    for word in words:
        trial = (line+' '+word).strip()
        if draw.textbbox((0,0), trial, font=font)[2] <= width: line=trial
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return lines

def txt(draw, xy, text, size, fill=INK, bold=False, width=None, gap=10):
    ft=f(size,bold)
    lines=wrap(draw,text,ft,width) if width else [text]
    x,y=xy
    for line in lines:
        draw.text((x,y),line,font=ft,fill=fill); y += size+gap
    return y

def header(c, draw, assets, kicker):
    add_logo(c, assets.get('logo',''), 64, 42)
    draw.text((1016,58), kicker, font=f(17,True), fill=BLUE, anchor='ra')
    draw.line((64,126,1016,126), fill='#C8D8E5', width=2)

def photo_panel(c, path, box, radius=26, cover=True, outline=None):
    x, y, w, h = box
    im = image(path, (w, h), cover)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    im = im.convert('RGBA'); im.putalpha(mask)
    c.alpha_composite(im, (x, y))
    if outline:
        ImageDraw.Draw(c).rounded_rectangle((x, y, x+w, y+h), radius=radius, outline=outline, width=3)

def label(draw, x, y, s):
    draw.rounded_rectangle((x,y,x+190,y+38), radius=19, fill=BLUE)
    draw.text((x+18,y+8), s.upper(), font=f(16,True), fill='white')

def card(draw, xy, size, title, body, accent=BLUE):
    x,y=xy; w,h=size
    draw.rounded_rectangle((x,y,x+w,y+h), radius=26, fill='white', outline='#D6E2EC', width=2)
    draw.rectangle((x,y,x+8,y+h), fill=accent)
    draw.text((x+30,y+25),title.upper(),font=f(18,True),fill=accent)
    txt(draw,(x+30,y+66),body,30,INK,True,w-60,8)

def make(data, assets, out):
    out.mkdir(parents=True, exist_ok=True)
    brand=value(data,'brand'); model=value(data,'model'); service=value(data,'service','service_performed')
    # 1: text-led cover, with a restrained evidence strip
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); header(c,d,assets,'CASE STUDY')
    d.rounded_rectangle((64,170,1016,790), radius=34, fill=NAVY)
    d.rectangle((64,170,82,790), fill=CYAN)
    d.text((112,220),brand.upper(),font=f(27,True),fill=CYAN)
    txt(d,(112,275),model or 'REMOTE VEHICLE PROGRAMMING',70,'white',True,820,5)
    txt(d,(112,455),service or 'Remote Automotive Engineering',34,'#DDEAF5',True,820,7)
    d.line((112,560,920,560),fill='#2C526F',width=2)
    txt(d,(112,605),'REMOTE PROGRAMMING\nCOMPLETED SUCCESSFULLY',39,'white',True,820,6)
    d.text((112,748),value(data,'location') or 'WORLDWIDE REMOTE SERVICE',font=f(20,True),fill=CYAN)
    photo_panel(c,assets.get('vehicle'),(64,850,952,380),28,True,'#A9C5DA')
    d.rounded_rectangle((88,1060,560,1198),radius=20,fill='#081827DD')
    d.text((120,1092),'REAL VEHICLE · SERVICE EVIDENCE',font=f(20,True),fill='white')
    c.convert('RGB').save(out/'01_case_cover.png',quality=95)

    # 2: problem page, text first, vertical photo as evidence
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); header(c,d,assets,'01 / CUSTOMER ISSUE')
    txt(d,(64,178),'WHAT NEEDED\nTO BE SOLVED',58,NAVY,True,900,2)
    d.rounded_rectangle((64,395,1016,710),radius=30,fill='white',outline='#D2E0EA',width=2)
    d.rectangle((64,395,82,710),fill=BLUE)
    d.text((112,438),'CUSTOMER ISSUE',font=f(19,True),fill=BLUE)
    txt(d,(112,490),value(data,'customer_issue') or 'Vehicle communication and module programming fault',37,INK,True,830,8)
    d.rounded_rectangle((64,760,490,890),radius=24,fill=BLUE)
    d.text((98,795),'FAULT CATEGORY',font=f(18,True),fill='#BFEFFF')
    txt(d,(98,830),value(data,'fault_category') or 'Communication Fault',28,'white',True,350,4)
    photo_panel(c,assets.get('fault'),(540,760,476,480),26,True,'#A9C5DA')
    c.convert('RGB').save(out/'02_customer_issue.png',quality=95)

    # 3: diagnosis page with asymmetry and a strong finding block
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); header(c,d,assets,'02 / DIAGNOSIS')
    txt(d,(64,178),'ROOT CAUSE\nIDENTIFIED',58,NAVY,True,900,2)
    photo_panel(c,assets.get('diagnosis'),(64,405,952,330),28,True,'#A9C5DA')
    d.rounded_rectangle((64,780,1016,1030),radius=30,fill=NAVY)
    d.text((104,825),'DIAGNOSTIC FINDING',font=f(19,True),fill=CYAN)
    txt(d,(104,878),value(data,'diagnosis') or 'Module communication and coding issue identified',35,'white',True,820,7)
    d.text((64,1110),'EQUIPMENT',font=f(19,True),fill=BLUE)
    txt(d,(64,1150),value(data,'equipment') or 'OEM Diagnostic Equipment',29,INK,True,900,7)
    c.convert('RGB').save(out/'03_diagnosis.png',quality=95)

    # 4: programming page; photo is a side proof rather than the main canvas
    c=Image.new('RGBA',(W,H),NAVY); d=ImageDraw.Draw(c)
    # On the dark programming card the white brand capsule is kept explicit;
    # it preserves the logo's fine light strokes at phone-size previews.
    d.rounded_rectangle((48,32,246,106), radius=18, fill='white')
    d.text((72,56),'DEATON',font=f(22,True),fill=NAVY)
    d.text((157,56),'AUTO',font=f(22,True),fill=BLUE)
    d.text((1016,60),'03 / PROGRAMMING',font=f(18,True),fill=CYAN,anchor='ra'); d.line((64,142,1016,142),fill='#29465F',width=2)
    txt(d,(64,180),'REMOTE\nPROGRAMMING',64,'white',True,900,2)
    txt(d,(64,420),'THE SERVICE',20,CYAN,True,900,8)
    txt(d,(64,465),service or 'Remote ECU Programming',42,'white',True,900,8)
    txt(d,(64,585),value(data,'programming_detail') or 'Remote programming performed and configuration restored',34,'#DCE8F3',True,850,8)
    photo_panel(c,assets.get('programming'),(64,820,952,350),28,True,'#4D789D')
    d.text((64,1260),'DEATON AUTO  ·  WORLDWIDE REMOTE PROGRAMMING',font=f(18,True),fill=CYAN)
    c.convert('RGB').save(out/'04_programming.png',quality=95)

    # 5: result page; clearly independent closing card
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); header(c,d,assets,'04 / VERIFIED RESULT')
    d.ellipse((64,205,148,289),fill=BLUE); d.text((106,246),'✓',font=f(52,True),fill='white',anchor='mm')
    txt(d,(180,210),'REPAIR\nCOMPLETED',60,NAVY,True,820,2)
    d.rounded_rectangle((64,400,1016,650),radius=30,fill='white',outline='#D2E0EA',width=2)
    d.text((104,445),'FINAL RESULT',font=f(19,True),fill=BLUE)
    txt(d,(104,495),value(data,'result','final_result') or 'Repair completed successfully',38,INK,True,830,8)
    d.rounded_rectangle((64,700,1016,850),radius=24,fill=BLUE)
    d.text((104,740),'VERIFICATION',font=f(18,True),fill='#BFEFFF')
    txt(d,(104,780),value(data,'verification') or 'Functions tested and verified',29,'white',True,830,4)
    photo_panel(c,assets.get('result'),(64,910,952,310),28,True,'#A9C5DA')
    c.convert('RGB').save(out/'05_verified_result.png',quality=95)
    return [str(p.resolve()) for p in sorted(out.glob('*.png'))]

if __name__ == '__main__':
    payload=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps({'files':make(payload['information'],payload['assets'],Path(payload['case_dir'])/'output-vertical')},ensure_ascii=False))
