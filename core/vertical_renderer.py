from __future__ import annotations

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
NAVY, BLUE, CYAN, INK, PALE = '#0B1B2B', '#1667D9', '#27B9E8', '#122236', '#F3F7FB'

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
    if m: c.alpha_composite(m, (x,y))

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
    add_logo(c, assets.get('logo',''))
    draw.text((790,60), kicker, font=f(18,True), fill=BLUE, anchor='ra')
    draw.line((64,142,1016,142), fill='#D8E4EF', width=2)

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
    c=Image.new('RGBA',(W,H),'white'); d=ImageDraw.Draw(c); header(c,d,assets,'CASE STUDY')
    d.text((64,205),brand.upper(),font=f(30,True),fill=BLUE)
    txt(d,(64,260),model or 'REMOTE VEHICLE PROGRAMMING',78,NAVY,True,850,7)
    txt(d,(64,490),service or 'Remote Automotive Engineering',38,BLUE,True,850,8)
    d.line((64,625,1016,625),fill='#D8E4EF',width=3)
    txt(d,(64,690),'REMOTE PROGRAMMING\nCOMPLETED SUCCESSFULLY',48,INK,True,850,10)
    d.text((64,870),value(data,'location') or 'WORLDWIDE REMOTE SERVICE',font=f(22,True),fill='#5B6B7B')
    im=image(assets.get('vehicle'),(952,270),True); c.alpha_composite(im.convert('RGBA'),(64,970))
    d.rectangle((64,970,1016,1240),outline=BLUE,width=3)
    c.convert('RGB').save(out/'01_case_cover.png',quality=95)

    # 2: problem page, text first, vertical photo as evidence
    c=Image.new('RGBA',(W,H),PALE); d=ImageDraw.Draw(c); header(c,d,assets,'01 / CUSTOMER ISSUE')
    txt(d,(64,205),'WHAT NEEDED\nTO BE SOLVED',64,NAVY,True,900,4)
    label(d,64,390,'CUSTOMER ISSUE')
    txt(d,(64,455),value(data,'customer_issue') or 'Vehicle communication and module programming fault',40,INK,True,900,10)
    card(d,(64,700),(952,210),'FAULT CATEGORY',value(data,'fault_category') or 'Communication Fault',BLUE)
    im=image(assets.get('fault'),(952,320),True); c.alpha_composite(im.convert('RGBA'),(64,1000)); d.rectangle((64,1000,1016,1320),outline='#B9CFE4',width=2)
    c.convert('RGB').save(out/'02_customer_issue.png',quality=95)

    # 3: diagnosis page with asymmetry and a strong finding block
    c=Image.new('RGBA',(W,H),'white'); d=ImageDraw.Draw(c); header(c,d,assets,'02 / DIAGNOSIS')
    txt(d,(64,205),'ROOT CAUSE\nIDENTIFIED',66,NAVY,True,900,4)
    im=image(assets.get('diagnosis'),(952,405),True); c.alpha_composite(im.convert('RGBA'),(64,475)); d.rectangle((64,475,1016,880),outline=BLUE,width=3)
    card(d,(64,930),(952,190),'DIAGNOSTIC FINDING',value(data,'diagnosis') or 'Module communication and coding issue identified',CYAN)
    d.text((64,1175),'EQUIPMENT',font=f(18,True),fill=BLUE)
    txt(d,(64,1215),value(data,'equipment') or 'OEM Diagnostic Equipment',28,INK,True,900,8)
    c.convert('RGB').save(out/'03_diagnosis.png',quality=95)

    # 4: programming page; photo is a side proof rather than the main canvas
    c=Image.new('RGBA',(W,H),NAVY); d=ImageDraw.Draw(c); add_logo(c,assets.get('logo',''),64,44)
    d.text((1016,60),'03 / PROGRAMMING',font=f(18,True),fill=CYAN,anchor='ra'); d.line((64,142,1016,142),fill='#29465F',width=2)
    txt(d,(64,205),'REMOTE\nPROGRAMMING',70,'white',True,900,4)
    txt(d,(64,420),'THE SERVICE',20,CYAN,True,900,8)
    txt(d,(64,465),service or 'Remote ECU Programming',42,'white',True,900,8)
    txt(d,(64,600),value(data,'programming_detail') or 'Remote programming performed and configuration restored',34,'#DCE8F3',True,850,10)
    im=image(assets.get('programming'),(952,360),True); c.alpha_composite(im.convert('RGBA'),(64,850)); d.rectangle((64,850,1016,1210),outline='#4D789D',width=3)
    d.text((64,1260),'DEATON AUTO  ·  WORLDWIDE REMOTE PROGRAMMING',font=f(18,True),fill=CYAN)
    c.convert('RGB').save(out/'04_programming.png',quality=95)

    # 5: result page; clearly independent closing card
    c=Image.new('RGBA',(W,H),'white'); d=ImageDraw.Draw(c); header(c,d,assets,'04 / VERIFIED RESULT')
    d.ellipse((64,205,148,289),fill=BLUE); d.text((106,246),'✓',font=f(52,True),fill='white',anchor='mm')
    txt(d,(180,210),'REPAIR\nCOMPLETED',66,NAVY,True,820,4)
    d.line((64,380,1016,380),fill=BLUE,width=5)
    txt(d,(64,450),value(data,'result','final_result') or 'Repair completed successfully',44,INK,True,900,10)
    card(d,(64,690),(952,190),'VERIFICATION',value(data,'verification') or 'Functions tested and verified',BLUE)
    im=image(assets.get('result'),(952,300),True); c.alpha_composite(im.convert('RGBA'),(64,960)); d.rectangle((64,960,1016,1260),outline='#B9CFE4',width=2)
    c.convert('RGB').save(out/'05_verified_result.png',quality=95)
    return [str(p.resolve()) for p in sorted(out.glob('*.png'))]

if __name__ == '__main__':
    payload=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    print(json.dumps({'files':make(payload['information'],payload['assets'],Path(payload['case_dir'])/'output-vertical')},ensure_ascii=False))
