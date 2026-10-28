"""Create the V3 campus film. Use -- preview to inspect seven shots first."""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).resolve().parent;W=O.parent/'work';D=W/'v3_film_frames';D.mkdir(exist_ok=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.use_persistent_data=True;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=24;s.frame_start=1;s.frame_end=1176;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=10;s.render.filepath=str(D/'frame_')
cam=bpy.data.objects.new('V3 Film camera',bpy.data.cameras.new('V3 Film camera'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.clip_end=10000;cam.rotation_mode='QUATERNION';s.camera=cam
shots=[
 ('全校鸟瞰',(25,-10,0),-20,0,54,57,1500,1400,['北园','南园']),
 ('历史建筑群',(145,170,5),-44,-28,49,53,480,435,['北大楼','东大楼','西大楼','大礼堂']),
 ('北大楼',(163,225,14),-78,-57,34,39,162,145,['北大楼']),
 ('校史博物馆',(194,-6,8),57,77,42,48,240,215,['校史博物馆','小礼堂']),
 ('南园',(210,-268,0),-64,-43,58,61,630,580,['南园','南园篮球场']),
 ('校园总图',(25,-10,0),0,0,89.8,89.8,1700,1650,['北园','南园','苏浙运动场','北大楼','汉口路']),
 ('回望鼓楼',(25,-10,0),0,-20,57,53,1400,1500,['北园','南园']),
]
annotations=json.load(open(O/'campus_annotations.json',encoding='utf8'));track={}
for k,(name,target,az0,az1,el0,el1,z0,z1,names) in enumerate(shots):
 s.timeline_markers.new(name,frame=k*168+1)
 for j in range(168):
  t=j/167;t=t*t*(3-2*t);az=math.radians(az0+(az1-az0)*t);el=math.radians(el0+(el1-el0)*t);v=Vector(target);r=1800
  cam.location=v+Vector((r*math.cos(el)*math.cos(az),r*math.cos(el)*math.sin(az),r*math.sin(el)));cam.rotation_quaternion=(v-cam.location).to_track_quat('-Z','Y');cam.data.ortho_scale=z0+(z1-z0)*t;f=k*168+j+1
  cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_quaternion',frame=f);cam.data.keyframe_insert('ortho_scale',frame=f);bpy.context.view_layer.update()
  track[str(f)]=[]
  for a in annotations:
   if a['name'] in names:
    pos=world_to_camera_view(s,cam,Vector(a['position']));track[str(f)].append({'name':a['name'],'x':pos.x,'y':1-pos.y})
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'NJU_Gulou_V3_Film.blend'))
json.dump(track,open(W/'v3_film_label_tracks.json','w',encoding='utf8'),ensure_ascii=False)
if 'preview' in sys.argv:
 for k in range(7):
  s.frame_set(k*168+84);s.render.filepath=str(W/f'v3_film_preview_{k}.png');bpy.ops.render.render(write_still=True)
else:
 s.render.filepath=str(D/'frame_');bpy.ops.render.render(animation=True)
