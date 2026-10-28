import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;s=bpy.context.scene
F=json.load(open(OUT/'campus_footprints.json'))
def inside(p,poly):
 x,y=p;c=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:c=not c
 return c
removed=0
for o in list(bpy.data.collections['12 Branching trees and planting'].objects):
 p=(o.location.x/.65+640,950-o.location.y/.65)
 if any(f['kind']=='sport' and any(inside(p,loop) for loop in f['loops']) for f in F):
  bpy.data.objects.remove(o,do_unlink=True);removed+=1
for o in bpy.data.collections['10 Landscape and street furniture'].objects:
 if any('Campus asphalt' in m.name for m in o.data.materials if m) if o.type=='MESH' else False:o.location.z+=.5
 if ' / curb' in o.name:o.location.z+=.5
for m in bpy.data.materials:
 if 'Campus asphalt' in m.name:
  m.diffuse_color=(.27,.30,.29,1)
  if m.use_nodes:m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.27,.30,.29,1)
cam=bpy.data.objects['V3 大礼堂近景'];cam.location=(252,166,102);cam.rotation_euler=(Vector((129,131,8))-cam.location).to_track_quat('-Z','Y').to_euler()
ann=json.load(open(OUT/'campus_annotations.json',encoding='utf8'));projected=json.load(open(OUT/'V3_projected_labels.json',encoding='utf8'))
cams=['V3 全校鸟瞰','V3 历史建筑群','V3 博物馆与图书馆','V3 南园生活区','V3 全校标注总图','V3 大礼堂近景']
s.cycles.samples=40
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU'
for (slug,item),name in zip(projected.items(),cams):
 s.camera=bpy.data.objects[name];s.render.resolution_x,s.render.resolution_y=item['size'];bpy.context.view_layer.update()
 for lab in item['labels']:
  a=next(a for a in ann if a['name']==lab['name']);p=world_to_camera_view(s,s.camera,Vector(a['position']));lab.update(x=p.x,y=1-p.y,depth=p.z)
 s.render.filepath=str(OUT/('V3_'+slug+'_clean.png'));bpy.ops.render.render(write_still=True)
json.dump(projected,open(OUT/'V3_projected_labels.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
s.camera=bpy.data.objects[cams[0]];s.render.resolution_x=2000;s.render.resolution_y=1800
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NJU_Gulou_Campus_V3.blend'))
print('FINALIZED removed court trees',removed,flush=True)
exec(compile((OUT/'export_v3_viewer.py').read_text(),str(OUT/'export_v3_viewer.py'),'exec'))
