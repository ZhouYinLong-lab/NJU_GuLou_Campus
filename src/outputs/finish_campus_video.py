"""Compose titles and a procedural original score over Blender frames.
Requires Python, Pillow, numpy and FFmpeg. Run after rendering animation.
"""
from pathlib import Path
import numpy as np, wave, subprocess, shutil, sys,json
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;WORK=OUT.parent/'work';FRAMES=WORK/'video_frames'
W,H,FPS,N=1280,720,24,1176
fontpaths=[Path('C:/Windows/Fonts/msyh.ttc'),Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')]
fontpath=next((str(p) for p in fontpaths if p.exists()),None)
font=lambda n:ImageFont.truetype(fontpath,n) if fontpath else ImageFont.load_default()
titles=[('梧桐深处，遇见南大','鼓楼校区 · 校园建筑沙盘'),('北园 · 历史与绿荫','沿着校园轴线，走近老建筑群'),('北大楼','灰瓦、钟楼与庭前草坪'),('苏浙运动场','跑道与球场之间的校园日常'),('南园 · 生活片区','汉口路以南，宿舍与公共空间'),('俯瞰鼓楼校区','南北园与西侧建筑群的空间关系'),('南京大学 · 鼓楼校区','一段校园漫游，一份立体记忆')]
def overlay(index):
 im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
 for y in range(150):
  a=int(224*max(0,1-y/150)**2);d.line((0,y,W,y),fill=(233,238,228,a))
 for y in range(H-180,H):
  a=int(232*((y-(H-180))/180)**1.5);d.line((0,y,W,y),fill=(233,238,228,a))
 ink=(39,60,53,255);muted=(91,108,92,255);purple=(85,52,111,255)
 d.rectangle((38,32,41,69),fill=purple)
 d.text((53,29),'南京大学 · 鼓楼校区',font=font(20),fill=ink)
 d.text((54,57),'NANJING UNIVERSITY / GULOU CAMPUS',font=font(9),fill=muted)
 d.text((1139,33),'3D 校园漫游',font=font(14),fill=ink)
 d.text((1196,57),'%02d / 07'%(index+1),font=font(11),fill=muted)
 d.text((40,620),titles[index][0],font=font(31),fill=ink)
 d.text((42,666),titles[index][1],font=font(14),fill=muted)
 d.text((1080,650),'公开地图与照片参考',font=font(11),fill=muted)
 d.text((1111,670),'近似建筑复原',font=font(11),fill=muted)
 for i in range(7):d.line((40+i*28,706,59+i*28,706),fill=purple if i==index else (135,150,134,150),width=2)
 return im
def score():
 sr=44100;duration=49;audio=np.zeros((sr*duration,2),dtype=np.float64)
 def note(midi,start,dur,amp,pan=.5,bell=False):
  n=int(dur*sr);t=np.arange(n)/sr;f=440*2**((midi-69)/12)
  attack=1-np.exp(-t/(.018 if bell else .32));release=np.minimum(1,np.maximum(0,(dur-t)/.8))
  env=attack*np.exp(-t/(1.35 if bell else 3.4))*release
  snd=(np.sin(2*np.pi*f*t)+.22*np.sin(2*np.pi*2*f*t)+.09*np.sin(2*np.pi*3*f*t))*env*amp
  pos=int(start*sr);end=min(len(audio),pos+n)
  if end<=pos:return
  snd=snd[:end-pos];audio[pos:end,0]+=snd*np.sqrt(1-pan);audio[pos:end,1]+=snd*np.sqrt(pan)
 chords=[[48,55,60,64],[45,52,57,60],[41,48,53,57],[43,50,55,59],[48,55,60,64],[41,48,53,57],[43,50,55,60]]
 for bar,chord in enumerate(chords):
  for pitch in chord:note(pitch,bar*7,8,.026,.5)
  for step in range(10):note(chord[step%4]+12,bar*7+step*.68,3.0,.047,.25+.5*(step%3)/2,True)
 # Stereo echo and soft fade: no borrowed recording or melody.
 delay=int(.37*sr);audio[delay:]+=.17*audio[:-delay,::-1].copy()
 t=np.arange(len(audio))/sr;audio*=np.minimum(1,t/2)[:,None]*np.minimum(1,(duration-t)/3)[:,None]
 peak=np.max(np.abs(audio));audio=audio/max(peak,.001)*.24
 with wave.open(str(WORK/'campus_original_score.wav'),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((audio*32767).astype('<i2').tobytes())
if 'assets' in sys.argv:
 score()
 for i,f in enumerate([1,220,390,550,720,890,1080]):
  im=Image.open(WORK/('film_preview_%04d.png'%f)).convert('RGBA');im=Image.alpha_composite(im,overlay(i));im.convert('RGB').save(WORK/('titled_preview_%d.jpg'%i),quality=93)
 print('Title previews and original music ready');sys.exit()
assert len(list(FRAMES.glob('frame_*.png')))==N,'Animation render incomplete'
score();ff=shutil.which('ffmpeg');assert ff
cmd=[ff,'-y','-hide_banner','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(WORK/'campus_original_score.wav'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-t','49',str(OUT/'NJU_Gulou_Campus_Film.mp4')]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE);overlays=[overlay(i) for i in range(7)]
paper=Image.new('RGB',(W,H),(222,231,222))
for frame in range(1,N+1):
 im=Image.open(FRAMES/('frame_%04d.png'%frame)).convert('RGBA');im=Image.alpha_composite(im,overlays[(frame-1)//168]).convert('RGB')
 fade=min(1,(frame-1)/18,(N-frame)/24)
 if fade<1:im=Image.blend(paper,im,max(0,fade))
 if frame==80:im.save(OUT/'campus_film_poster.jpg',quality=95)
 p.stdin.write(im.tobytes())
 if frame%168==0:print('Composited shot',frame//168,flush=True)
p.stdin.close();assert p.wait()==0
probe=subprocess.run([shutil.which('ffprobe'),'-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',str(OUT/'NJU_Gulou_Campus_Film.mp4')],capture_output=True,text=True,check=True)
info=json.loads(probe.stdout);assert abs(float(info['format']['duration'])-49)<.1
json.dump(info,open(OUT/'video_validation.json','w'),indent=2)
print('VIDEO_COMPLETE',info)
