from pathlib import Path
import base64,json
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;W=O.parent/'work'
def font(n):
 for p in [Path('C:/Windows/Fonts/msyh.ttc'),Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')]:
  if p.exists():return ImageFont.truetype(str(p),n)
 return ImageFont.load_default()
data=json.loads((O/'V3_projected_labels.json').read_text(encoding='utf8'))
titles={'overview':'全校鸟瞰','heritage':'历史建筑群','museum':'校史博物馆与图书馆','south':'南园生活区','plan':'校园建筑总图','auditorium':'大礼堂 · 屋面与入口'}
for slug,v in data.items():
 im=Image.open(O/f'V3_{slug}_clean.png').convert('RGBA');w,h=im.size;overlay=Image.new('RGBA',im.size);d=ImageDraw.Draw(overlay)
 # Quiet header wash, preserving the entire rendered frame.
 for y in range(190):d.line((0,y,w,y),fill=(241,244,236,int(215*(1-y/190))))
 d.text((62,37),'NANJING UNIVERSITY  /  GULOU CAMPUS',font=font(16),fill='#53685b')
 d.text((60,66),'南京大学 · 鼓楼校区',font=font(42),fill='#243e30')
 d.text((63,125),titles[slug]+'   /   模型细化与标注 V3',font=font(21),fill='#53685b')
 labs=[l for l in v['labels'] if .025<l['x']<.975 and .12<l['y']<.94];occupied=[]
 if slug=='plan':
  sides=[sorted([l for l in labs if l['x']<.51],key=lambda a:a['y']),sorted([l for l in labs if l['x']>=.51],key=lambda a:a['y'])]
  for side,ls in enumerate(sides):
   last=185
   for l in ls:
    px,py=l['x']*w,l['y']*h;ty=max(last, min(h-95,py));last=ty+52;tx=65 if side==0 else w-300;l['fixed']=(tx,ty)
 for l in labs:
  px,py=l['x']*w,l['y']*h;name=l['name'];f=font(23);tw=d.textbbox((0,0),name,font=f)[2]+28;th=44
  if 'fixed' in l:tx,ty=l['fixed']
  else:
   candidates=[(px+26,py-58),(px-tw-26,py-58),(px+28,py+20),(px-tw-28,py+20),(px-tw/2,py-98)]
   tx,ty=candidates[0]
   for x,y in candidates:
    b=(x,y,x+tw,y+th)
    if 24<x<w-tw-24 and 180<y<h-95 and not any(b[0]<a[2]+12 and b[2]>a[0]-12 and b[1]<a[3]+12 and b[3]>a[1]-12 for a in occupied):tx,ty=x,y;break
  box=(tx,ty,tx+tw,ty+th);occupied.append(box);endx=tx if px<tx else tx+tw if px>tx+tw else px;endy=ty+th/2
  d.line([(px,py),(px+(endx-px)*.55,endy),(endx,endy)],fill=(60,85,64,210),width=2);d.ellipse((px-4,py-4,px+4,py+4),fill='#31543a',outline='#f8faef',width=2)
  d.rounded_rectangle(box,radius=5,fill=(247,249,240,237),outline=(255,255,255,230),width=1);d.text((tx+14,ty+7),name,font=f,fill='#2c4735')
 d.text((63,h-58),'依据南京大学校园地图及校史档案建模  ·  展示级外观模型',font=font(17),fill='#556b5c');d.text((w-175,h-58),'静态审阅',font=font(17),fill='#556b5c')
 Image.alpha_composite(im,overlay).convert('RGB').save(O/f'V3_{slug}_annotated.png')
html=(O/'viewer_template.html').read_text(encoding='utf8').replace('__ANNOTATIONS__',(O/'campus_annotations.json').read_text(encoding='utf8')).replace('__BUNDLE__',(W/'viewer.bundle.js').read_text(encoding='utf8')).replace('__MODEL__',base64.b64encode((O/'NJU_Gulou_Campus_V3.glb').read_bytes()).decode())
(O/'NJU_Gulou_Viewer.html').write_text(html,encoding='utf8')
print('Annotated images and offline viewer ready')
