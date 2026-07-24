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

def add_logo(c, path, x=64, y=42):
    # The current personal-brand direction uses YH; do not reuse the legacy
    # DA/Deaton Auto artwork in social case images.
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((x-14, y-8, x+112, y+58), radius=18, fill=NAVY)
    d.text((x+16, y+4), 'YH', font=f(34, True), fill='white')
    d.rectangle((x+77, y+13, x+82, y+45), fill=CYAN)

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
    def full_photo(path, box=(0,0,W,H)):
        x,y,w,h=box; im=image(path,(w,h),True).convert('RGBA'); c.alpha_composite(im,(x,y))
    def shade(box, fill=(8,24,39,190), radius=0):
        layer=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(layer)
        if radius: ld.rounded_rectangle(box,radius=radius,fill=fill)
        else: ld.rectangle(box,fill=fill)
        c.alpha_composite(layer)
    def brand_mark(d, dark=False):
        fill='white' if dark else NAVY; ink=NAVY if dark else 'white'
        d.rounded_rectangle((54,42,174,106),radius=18,fill=fill)
        d.text((78,52),'YH',font=f(30,True),fill=ink)
        d.rectangle((142,56,147,92),fill=CYAN)
    def slide_no(d, s, dark=False):
        d.text((1018,61),s,font=f(17,True),fill=CYAN if dark else BLUE,anchor='ra')

    # 1: full-bleed cover: the photo is the canvas, text sits in its dark space.
    c=Image.new('RGBA',(W,H),NAVY); full_photo(assets.get('vehicle')); shade((0,0,W,600),(5,19,31,205)); shade((0,830,W,H),(5,19,31,220))
    d=ImageDraw.Draw(c); brand_mark(d,True); slide_no(d,'CASE STUDY',True)
    d.text((66,190),brand.upper() or 'BMW',font=f(28,True),fill=CYAN)
    txt(d,(64,245),model or 'REMOTE VEHICLE\nPROGRAMMING',68,'white',True,850,3)
    d.line((64,520,440,520),fill=CYAN,width=5)
    txt(d,(64,900),service or 'Remote Programming',34,'white',True,850,6)
    txt(d,(64,982),'REMOTE PROGRAMMING\nCOMPLETED SUCCESSFULLY',43,'white',True,900,4)
    d.text((64,1190),value(data,'location') or 'WORLDWIDE REMOTE SERVICE',font=f(21,True),fill=CYAN)
    c.convert('RGB').save(out/'01_case_cover.png',quality=95)

    # 2: issue page: image is dominant, issue label is anchored to it.
    c=Image.new('RGBA',(W,H),NAVY); full_photo(assets.get('fault')); shade((0,0,W,H),(4,18,30,85)); shade((0,720,W,H),(4,18,30,215))
    d=ImageDraw.Draw(c); brand_mark(d,True); slide_no(d,'01 / CUSTOMER ISSUE',True)
    d.text((64,790),'CUSTOMER ISSUE',font=f(22,True),fill=CYAN)
    txt(d,(64,842),value(data,'customer_issue') or 'Communication fault',48,'white',True,900,5)
    d.line((64,1015,520,1015),fill=CYAN,width=5)
    d.text((64,1050),'FAULT CATEGORY',font=f(18,True),fill='#BFEFFF')
    txt(d,(64,1090),value(data,'fault_category') or 'Communication Fault',31,'white',True,850,5)
    c.convert('RGB').save(out/'02_customer_issue.png',quality=95)

    # 3: diagnosis page: a clean split screen, with finding carried on the photo edge.
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); brand_mark(d); slide_no(d,'02 / DIAGNOSIS')
    photo_panel(c,assets.get('diagnosis'),(0,170,1080,650),0,True)
    shade((0,170,1080,820),(8,24,39,35))
    d.rounded_rectangle((54,690,1026,1030),radius=34,fill=NAVY)
    d.text((94,744),'ROOT CAUSE IDENTIFIED',font=f(21,True),fill=CYAN)
    txt(d,(94,798),value(data,'diagnosis') or 'Communication fault identified',40,'white',True,850,6)
    d.line((94,930,520,930),fill='#456A83',width=2)
    d.text((94,966),'EQUIPMENT',font=f(17,True),fill='#A9CFE5')
    txt(d,(94,1000),value(data,'equipment') or 'OEM Diagnostic Equipment',28,'white',True,820,4)
    d.rounded_rectangle((54,1120,1026,1260),radius=24,fill='#DCEAF2')
    d.text((94,1150),'DIAGNOSTIC WORKFLOW',font=f(17,True),fill=BLUE)
    d.text((94,1192),'SCAN  ·  IDENTIFY  ·  CONFIGURE',font=f(25,True),fill=NAVY)
    c.convert('RGB').save(out/'03_diagnosis.png',quality=95)

    # 4: programming page: photo cuts through the copy instead of sitting below it.
    c=Image.new('RGBA',(W,H),NAVY); d=ImageDraw.Draw(c); brand_mark(d,True); slide_no(d,'03 / PROGRAMMING',True)
    txt(d,(64,190),'REMOTE\nPROGRAMMING',64,'white',True,900,2)
    d.text((64,430),'THE SERVICE',font=f(20,True),fill=CYAN)
    txt(d,(64,478),service or 'Remote ECU Programming',40,'white',True,900,6)
    photo_panel(c,assets.get('programming'),(64,650,952,390),28,True,'#4D789D')
    d.rounded_rectangle((64,1010,1016,1200),radius=26,fill='#102F49')
    d.text((98,1050),'PROCESS',font=f(18,True),fill=CYAN)
    txt(d,(98,1090),value(data,'programming_detail') or 'Remote programming performed and configuration restored',30,'white',True,830,5)
    d.text((64,1260),'YH  ·  WORLDWIDE REMOTE PROGRAMMING',font=f(18,True),fill=CYAN)
    c.convert('RGB').save(out/'04_programming.png',quality=95)

    # 5: result page: photo and verified outcome share one closing composition.
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); brand_mark(d); slide_no(d,'04 / VERIFIED RESULT')
    d.ellipse((64,190,154,280),fill=BLUE); d.text((109,235),'✓',font=f(52,True),fill='white',anchor='mm')
    txt(d,(190,194),'REPAIR\nCOMPLETED',58,NAVY,True,820,2)
    photo_panel(c,assets.get('result'),(0,430,1080,430),0,True)
    shade((0,430,1080,860),(8,24,39,45))
    d.rounded_rectangle((54,800,1026,1110),radius=34,fill=NAVY)
    d.text((94,850),'FINAL RESULT',font=f(20,True),fill=CYAN)
    txt(d,(94,902),value(data,'result','final_result') or 'Repair completed successfully',39,'white',True,850,6)
    d.line((94,1005,520,1005),fill='#456A83',width=2)
    d.text((94,1040),'VERIFICATION',font=f(17,True),fill='#A9CFE5')
    txt(d,(94,1075),value(data,'verification') or 'Functions tested and verified',29,'white',True,820,4)
    d.rounded_rectangle((54,1170,1026,1280),radius=24,fill='#DCEAF2')
    d.text((94,1200),'DEATON AUTO  ·  REMOTE VEHICLE PROGRAMMING',font=f(18,True),fill=NAVY)
    c.convert('RGB').save(out/'05_verified_result.png',quality=95)
    return [str(p.resolve()) for p in sorted(out.glob('*.png'))]

if __name__ == '__main__':
    payload=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps({'files':make(payload['information'],payload['assets'],Path(payload['case_dir'])/'output-vertical')},ensure_ascii=False))
