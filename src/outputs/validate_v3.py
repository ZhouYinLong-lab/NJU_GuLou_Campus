import bpy,json,struct
from pathlib import Path
O=Path(__file__).resolve().parent;s=bpy.context.scene
bad={'南大浴室教育超市','华龙楼3号幼儿园','综合服务','信息管理','后勤服务','品商店','物理楼新变电所','物理楼物理楼','人工微结构科学','赛珍'}
a=json.load(open(O/'campus_annotations.json',encoding='utf8'));a=[p for p in a if p['name'] not in bad]
json.dump(a,open(O/'campus_annotations.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
for o in list(bpy.data.collections['11 Verified map annotations'].objects):
 if any(o.name.endswith(n) for n in bad):bpy.data.objects.remove(o,do_unlink=True)
s['annotation_count']=len(a)
stats=json.load(open(O/'V3_stats.json'));stats['annotations']=len(a);stats['objects']=len(s.objects);json.dump(stats,open(O/'V3_stats.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'NJU_Gulou_Campus_V3.blend'))
required=['北大楼 / detailed assembly','东大楼','西大楼','大礼堂','校史博物馆 · 原金陵大学图书馆','小礼堂','西南楼','东北楼']
report={'landmarks':{n:n in bpy.data.objects for n in required},'annotations':len(a),'packed_fonts':len(bpy.data.fonts),'static_cameras':len([o for o in s.objects if o.type=='CAMERA' and o.name.startswith('V3 ')]),'video_created':False}
with open(O/'NJU_Gulou_Campus_V3.glb','rb') as f:
 magic,version,length=struct.unpack('<4sII',f.read(12));size,typ=struct.unpack('<II',f.read(8));g=json.loads(f.read(size));report['glb']={'version':version,'valid_size':length==(O/'NJU_Gulou_Campus_V3.glb').stat().st_size,'meshes':len(g.get('meshes',[])),'animations':len(g.get('animations',[]))}
assert all(report['landmarks'].values());assert len(a)==len(set(p['name'] for p in a));assert report['glb']['valid_size'];assert report['glb']['animations']==0
json.dump(report,open(O/'V3_model_validation.json','w',encoding='utf8'),ensure_ascii=False,indent=2);print(report)
