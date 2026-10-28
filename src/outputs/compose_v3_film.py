"""Composite tracked labels and an original instrumental score over V3 renders."""
from pathlib import Path
import ast,json,subprocess,shutil,wave,sys,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;WORK=OUT.parent/'work';FRAMES=WORK/'v3_film_gpu_frames';W,H,FPS,N=1920,1080,24,1176
def font(n):
 for p in [Path('C:/Windows/Fonts/msyh.ttc'),Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')]:
  if p.exists():return ImageFont.truetype(str(p),n)
 return ImageFont.load_default()
tracks=json.load(open(WORK/'v3_film_label_tracks.json',encoding='utf8'))
titles=[('梧桐深处，遇见南大','鼓楼校区 · 校园建筑微缩模型'),('北园 · 历史建筑群','北大楼、东大楼、西大楼与大礼堂'),('北大楼','灰瓦、塔楼、红星与庭前绿荫'),('校史博物馆','原金陵大学图书馆 · 门厅与重檐'),('南园 · 生活片区','汉口路以南的宿舍与公共空间'),('俯瞰鼓楼校区','南北园与西侧建筑群的空间关系'),('南京大学 · 鼓楼校区','一段校园漫游，一份立体记忆')]
def overlay(k):
 im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
 for y in range(210):d.line((0,y,W,y),fill=(237,242,231,int(228*(1-y/210)**1.5)))
 for y in range(835,H):d.line((0,y,W,y),fill=(237,242,231,int(240*((y-835)/(H-835))**1.25)))
 ink='#273f32';muted='#61745f';accent='#68497c'
 d.rectangle((58,48,62,101),fill=accent);d.text((80,42),'南京大学 · 鼓楼校区',font=font(30),fill=ink);d.text((81,87),'NANJING UNIVERSITY / GULOU CAMPUS',font=font(14),fill=muted)
 d.text((1715,48),'3D 校园漫游',font=font(21),fill=ink);d.text((1785,85),f'{k+1:02d} / 07',font=font(16),fill=muted)
 d.text((61,931),titles[k][0],font=font(46),fill=ink);d.text((64,1000),titles[k][1],font=font(22),fill=muted)
 d.text((1617,978),'依据公开地图与校史档案',font=font(17),fill=muted);d.text((1668,1009),'展示级建筑外观模型',font=font(17),fill=muted)
 for i in range(7):d.line((62+i*42,1060,89+i*42,1060),fill=accent if i==k else '#a4b09c',width=3)
 return im
overlays=[overlay(k) for k in range(7)]
def compose(f,preview=False):
 k=(f-1)//168;p=WORK/f'v3_film_preview_{k}.png' if preview else FRAMES/f'frame_{f:04d}.png'
 while not p.exists() or time.time()-p.stat().st_mtime<.3:time.sleep(.2)
 im=Image.open(p).convert('RGBA');layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer);used=[]
 for a in tracks[str(f)]:
  x,y=a['x']*W,a['y']*H
  if not 55<x<W-180 or not 185<y<825:continue
  tw=d.textbbox((0,0),a['name'],font=font(22))[2]+28;tx=x+23;ty=y-48
  for step in range(4):
   box=(tx,ty,tx+tw,ty+40)
   if not any(box[0]<b[2]+8 and box[2]>b[0]-8 and box[1]<b[3]+8 and box[3]>b[1]-8 for b in used):break
   ty-=46
  if ty<150:continue
  used.append(box);d.line((x,y,tx,ty+25),fill=(49,80,56,210),width=2);d.ellipse((x-3,y-3,x+3,y+3),fill='#35573c');d.rounded_rectangle(box,radius=4,fill=(246,249,236,228));d.text((tx+14,ty+6),a['name'],font=font(22),fill='#304d35')
 return Image.alpha_composite(Image.alpha_composite(im,layer),overlays[k]).convert('RGB')
if 'preview' in sys.argv:
 board=Image.new('RGB',(1440,1080),'#e9eee5')
 for k in range(7):
  im=compose(k*168+84,True);im.save(WORK/f'v3_film_titled_{k}.jpg',quality=94);im.thumbnail((480,270));board.paste(im,((k%3)*480,(k//3)*270))
 board.save(WORK/'v3_film_storyboard.jpg',quality=94);sys.exit()
# Frames are consumed as the renderer completes them.
# Reuse only the original synthesizer function, without executing the old film script.
tree=ast.parse((OUT/'finish_campus_video.py').read_text(encoding='utf8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='score');exec(compile(ast.Module(body=[fn],type_ignores=[]),'<original score>','exec'));score()
ff=shutil.which('ffmpeg');dest=OUT/'NJU_Gulou_V3_Film.mp4'
p=subprocess.Popen([ff,'-y','-hide_banner','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','24','-i','pipe:0','-i',str(WORK/'campus_original_score.wav'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-t','49',str(dest)],stdin=subprocess.PIPE)
paper=Image.new('RGB',(W,H),(229,237,226))
for f in range(1,N+1):
 im=compose(f);j=(f-1)%168
 if f>168 and j<12:im=Image.blend(compose(f-12),im,(j+1)/12)
 fade=min(1,(f-1)/20,(N-f)/28)
 if fade<1:im=Image.blend(paper,im,max(0,fade))
 if f==84:im.save(OUT/'V3_film_poster.jpg',quality=95)
 p.stdin.write(im.tobytes())
 if f%168==0:print('COMPOSED',f,flush=True)
p.stdin.close();assert p.wait()==0
probe=subprocess.run([shutil.which('ffprobe'),'-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',str(dest)],capture_output=True,text=True,check=True);info=json.loads(probe.stdout);assert abs(float(info['format']['duration'])-49)<.1
json.dump(info,open(OUT/'V3_film_validation.json','w'),indent=2);print('V3_FILM_COMPLETE',info)
