"""Export a compact static GLB from the V3 Blender scene."""
import bpy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;s=bpy.context.scene
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o.type in ['MESH','CURVE'] and not o.hide_render and o.name!='Studio floor':o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in bpy.context.selected_objects if o.type=='MESH')
bpy.ops.object.convert(target='MESH')
selected=list(bpy.context.selected_objects);groups={}
for o in selected:
 if o.type!='MESH':continue
 if any(c.name.startswith('12 ') for c in o.users_collection):continue
 if o.parent:key=o.parent.name
 else:key=o.users_collection[0].name if o.users_collection else 'site'
 groups.setdefault(key,[]).append(o)
for name,objs in groups.items():
 if len(objs)<2:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();bpy.context.object.name=name
# Preserve tree mesh sharing; export visible static geometry and its parent transforms.
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o.type=='MESH' and not o.hide_render and o.name!='Studio floor':
  o.select_set(True);p=o.parent
  while p:p.select_set(True);p=p.parent
bpy.ops.export_scene.gltf(filepath=str(OUT/'NJU_Gulou_Campus_V3.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_animations=False,export_extras=True)
print('V3_GLB_EXPORTED',(OUT/'NJU_Gulou_Campus_V3.glb').stat().st_size)
