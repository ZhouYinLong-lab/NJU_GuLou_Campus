"""Run on the saved .blend to validate and export a portable GLB."""
import bpy,json,math
from pathlib import Path
out=Path(__file__).resolve().parent
scene=bpy.context.scene
assert len(bpy.data.objects)>1000
assert len([o for o in bpy.data.objects if o.type=='CAMERA'])==4
assert all(all(math.isfinite(v) for v in o.location) for o in bpy.data.objects)
assert bpy.data.objects.get('Central tower stone shaft')
report={'reopened_blend':True,'objects':len(bpy.data.objects),'cameras':4,'packed_fonts':sum(f.packed_file is not None for f in bpy.data.fonts),'checks':'finite transforms, landmark presence, scene object count, four cameras'}
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH','CURVE','FONT'} and o.name!='Studio floor':o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in bpy.context.selected_objects)
bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(out/'NJU_Gulou_Campus.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
assert (out/'NJU_Gulou_Campus.glb').stat().st_size>100000
report['glb_bytes']=(out/'NJU_Gulou_Campus.glb').stat().st_size
json.dump(report,open(out/'validation.json','w'),indent=2)
print('VALIDATED',report)
