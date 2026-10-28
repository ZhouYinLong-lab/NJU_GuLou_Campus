import bpy,time
from pathlib import Path
O=Path(__file__).resolve().parent;D=O.parent/'work'/'v3_film_gpu_frames';D.mkdir(exist_ok=True);s=bpy.context.scene
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.denoiser='OPTIX';s.cycles.samples=16;s.render.use_persistent_data=True;t=time.monotonic()
for f in range(1,1177):
 dest=D/f'frame_{f:04d}.png'
 if dest.exists() and dest.stat().st_size>10000:continue
 s.frame_set(f);s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
 if f%24==0:print('FILM_PROGRESS',f,1176,'elapsed',round(time.monotonic()-t),flush=True)
print('RENDER_COMPLETE',flush=True)
