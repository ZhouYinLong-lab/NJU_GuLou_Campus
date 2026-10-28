"""Refine the campus using NJU Archives plans/elevations and photographs.
Run on NJU_Gulou_Campus.blend. Produces a separate editable V2 study.
North Building dimensions transcribed from the published elevation images;
fine ornament and vegetation remain approximate.
"""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
random.seed(1919)
OUT=Path(__file__).resolve().parent
s=bpy.context.scene
C=bpy.data.collections.new('08 North Building - archive-based detail');s.collection.children.link(C)
x,y=163.15,229.45;angle=.12
root=bpy.data.objects.new('北大楼 / detailed assembly',None);C.objects.link(root);root.location=(x,y,.65);root.rotation_euler.z=angle
root['source']='https://dawww.nju.edu.cn/info/1201/10711.htm';root['main_width_m']=64.565;root['eaves_height_m']=9.675;root['main_ridge_m']=18.915;root['tower_finial_m']=32.225
# Remove only the first version of North Building, using world-space bounds.
removed=[]
for o in list(bpy.data.collections['03 Heritage landmarks'].objects):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(pts,Vector())/8
    if 125<center.x<201 and 209<center.y<249:
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
def material(name,color,rough=.6):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
brick=material('V2 Ming city brick / 青灰明城砖',(.23,.24,.20));stone=material('V2 Pale carved stone',(.49,.48,.39));dark=material('V2 Deep window reveal',(.027,.033,.024));wood=material('V2 Oxblood wooden sash',(.16,.045,.026));glass=material('V2 Muted window glass',(.105,.18,.19),.22);roof=material('V2 Weathered grey clay tiles',(.17,.20,.19));red=material('V2 Red metal star',(.62,.012,.018),.38);lattice=material('V2 Gable ochre timber lattice',(.45,.255,.07))
ivy=[material('V2 Ivy %d'%i,c) for i,c in enumerate([(.065,.135,.027),(.13,.20,.035),(.23,.28,.055),(.28,.23,.05),(.30,.12,.035)])]
# Physical-scale brick courses, mapped along each vertical wall orientation.
nt=brick.node_tree;nodes=nt.nodes;links=nt.links;p=nodes.get('Principled BSDF')
tex=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(tex.outputs['Object'],sep.inputs[0]);geo=nodes.new('ShaderNodeNewGeometry');norm=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],norm.inputs[0]);ab=nodes.new('ShaderNodeMath');ab.operation='ABSOLUTE';links.new(norm.outputs['X'],ab.inputs[0]);cmp=nodes.new('ShaderNodeMath');cmp.operation='GREATER_THAN';links.new(ab.outputs[0],cmp.inputs[0]);cmp.inputs[1].default_value=.5
mix=nodes.new('ShaderNodeMixRGB');links.new(cmp.outputs[0],mix.inputs[0]);links.new(sep.outputs['X'],mix.inputs[1]);links.new(sep.outputs['Y'],mix.inputs[2]);comb=nodes.new('ShaderNodeCombineXYZ');links.new(mix.outputs[0],comb.inputs[0]);links.new(sep.outputs['Z'],comb.inputs[1])
br=nodes.new('ShaderNodeTexBrick');links.new(comb.outputs[0],br.inputs['Vector']);br.inputs['Scale'].default_value=1;br.inputs['Brick Width'].default_value=.64;br.inputs['Row Height'].default_value=.25;br.inputs['Mortar Size'].default_value=.009;br.inputs['Mortar Smooth'].default_value=.025;br.inputs['Color1'].default_value=(.24,.25,.22,1);br.inputs['Color2'].default_value=(.15,.17,.155,1);br.inputs['Mortar'].default_value=(.10,.115,.10,1);links.new(br.outputs['Color'],p.inputs['Base Color']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.42;bump.inputs['Distance'].default_value=.06;links.new(br.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
for m in [stone,roof]:
    nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=23;n.inputs['Detail'].default_value=3;b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.18;b.inputs['Distance'].default_value=.045;nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal'])
batch={}
def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);C.objects.link(o);o.parent=root;o.data.materials.append(mat);return o
def addbox(name,center,dims,mat):
    # Batch cuboids by semantic component and material, retain useful editing groups.
    vs,fs=batch.setdefault((name,mat.name),([],[]));a=len(vs);cx,cy,cz=center;w,d,h=[v/2 for v in dims]
    vs.extend([(cx+xx*w,cy+yy*d,cz+zz*h) for xx,yy,zz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
    fs.extend([tuple(a+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
def curve(name,pts,r,mat):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;cu.use_fill_caps=True;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for pt,v in zip(sp.points,pts):pt.co=(*v,1)
    o=bpy.data.objects.new(name,cu);C.objects.link(o);o.parent=root;cu.materials.append(mat);return o
def wall(name,span,zmax,depth,openings,rotation=0):
    # Explicit openings, not dark rectangles pasted onto a solid wall.
    xs=sorted(set([-span/2,span/2]+[v for op in openings for v in op[:2]]));zs=sorted(set([0,zmax]+[v for op in openings for v in op[2:]]))
    vs=[];fs=[]
    for a,b in zip(xs,xs[1:]):
        for lo,hi in zip(zs,zs[1:]):
            mid=((a+b)/2,(lo+hi)/2)
            if any(l<mid[0]<r and bot<mid[1]<top for l,r,bot,top in openings):continue
            addbox(name,(mid[0],depth,mid[1]),(b-a,.55,hi-lo),brick)
def window(cx,yy,z,w,h,name='Main sash'):
    addbox('Recess backing',(cx,yy+.28,z),(w,.09,h),dark)
    addbox('Glazing',(cx,yy+.075,z),(w-.12,.065,h-.12),glass)
    for dx in [-w/2,w/2]:addbox(name,(cx+dx,yy-.025,z),(.085,.16,h+.1),wood)
    for dz in [-h/2,0,h/2]:addbox(name,(cx,yy-.03,z+dz),(w+.085,.16,.08),wood)
    for dx in [-w/6,w/6]:addbox('Fine wooden mullions',(cx+dx,yy-.04,z),(.035,.11,h),wood)
    for dz in [-h/3,h/3]:addbox('Fine wooden mullions',(cx,yy-.04,z+dz),(w,.11,.035),wood)
    addbox('Stone lintels',(cx,yy-.045,z+h/2+.13),(w+.30,.39,.20),stone)
    addbox('Projecting stone sills',(cx,yy-.11,z-h/2-.11),(w+.26,.52,.15),stone)
positions=[sign*(6.6+j*2.16) for sign in [-1,1] for j in range(12)]
opens=[(a-.64,a+.64,z-h/2,z+h/2) for a in positions for z,h in [(2.6,2.8),(7.25,3.0)]]
wall('Front perforated masonry',64.565,9.675,-9.4,opens)
wall('Rear perforated masonry',64.565,9.675,9.4,opens)
for a in positions:
    for z,h in [(2.6,2.8),(7.25,3)]:window(a,-9.48,z,1.28,h)
# Rear sash assembly mirrored from front, using batched mirrored components.
for (name,matname),(vs,fs) in list(batch.items()):
    if name in ['Main sash','Recess backing','Glazing','Fine wooden mullions','Stone lintels','Projecting stone sills']:
        n=len(vs);back=[(a,-b,c) for a,b,c in vs];vs.extend(back);fs.extend([tuple(n+i for i in reversed(f)) for f in fs.copy()])
for xx in [-32.28,32.28]:addbox('End walls',(xx,0,4.8375),(.55,18.8,9.675),brick)
for zz,hh,dd in [(.3,.6,19.4),(.85,.22,19.1),(4.565,.27,19.25),(9.30,.27,19.5),(9.65,.20,19.8)]:addbox('Horizontal masonry courses',(0,0,zz),(65,dd,hh),stone)
for zz in [.1,4.565,9.675]:addbox('Interior floor plates',(0,0,zz),(64,18.2,.17),dark)
# Tower: five-storey square shaft; upper three windows and stone false balcony.
tw=9.4;front=-12.0;back=-2.6
tops=[(-3.35,-1.25,22.0,24.25),(-1.05,1.05,22.0,24.25),(1.25,3.35,22.0,24.25)]
topen=[(-2.0,2.0,.6,4.3),(-2.1,2.1,5.6,8.5),(-.70,.70,12.35,14.85),(-.70,.70,17.75,20.10)]+tops
wall('Tower front pierced masonry',tw,25.205,front,topen)
wall('Tower rear masonry',tw,25.205,back,[])
for xx in [-4.7,4.7]:addbox('Tower side masonry',(xx,(front+back)/2,12.6),(.55,9.4,25.2),brick)
for xx in [-4.62,4.62]:addbox('Tower corner pilaster',(xx,front-.11,12.4),(.36,.22,24.8),stone)
window(0,front-.08,13.6,1.4,2.5);window(0,front-.08,18.925,1.4,2.35)
for a in [-2.3,0,2.3]:window(a,front-.08,23.125,2.1,2.25,'Tower sash')
for a in [-1.4,0,1.4]:window(a,front-.08,7.05,1.25,2.9,'Entrance upper windows')
addbox('Entry deep shadow',(0,front+.15,2.3),(4,.1,3.6),dark)
for a in [-.91,.91]:
    addbox('Double entrance door',(a,front-.08,2.15),(1.75,.18,3.05),wood)
    for z in [1.35,2.50]:addbox('Door recessed panels',(a,front-.19,z),(1.35,.06,.82),dark)
for a in [-2.2,2.2]:addbox('Entry stone door surround',(a,front-.2,2.45),(.30,.7,4.2),stone)
addbox('Entry pediment lintel',(0,front-.2,4.65),(4.7,.8,.5),stone)
for j in range(5):addbox('Entry broad stone steps',(0,front-1.3-j*.37,.50-j*.1),(5.5+j*.25,.55,.18),stone)
for z in [5.25,21.35]:
    addbox('False balcony stone platform',(0,front-.48,z),(6.25,1.15,.25),stone)
    for xx in [-3,-2,-1,0,1,2,3]:addbox('Balcony stone balusters',(xx,front-.92,z+.57),(.13,.18,.94),stone)
    addbox('Balcony carved handrail',(0,front-.92,z+1.02),(6.4,.30,.16),stone)
    addbox('Balcony base band',(0,front-.92,z+.2),(6.3,.25,.15),stone)
# Side balconies, upper sash and rectangular shallow reliefs.
for sign in [-1,1]:
    for a in [-9.6,-7.3,-5.0]:
        addbox('Tower side window stone border',(sign*4.99,a,23.1),(.18,2.2,2.4),stone)
        addbox('Tower side dark wooden sash',(sign*5.10,a,23.1),(.10,1.9,2.16),wood)
        addbox('Tower side glazing',(sign*5.16,a,23.1),(.05,1.6,1.85),glass)
        for dz in [-.55,0,.55]:addbox('Tower side sash bars',(sign*5.20,a,23.1+dz),(.06,1.8,.05),wood)
    addbox('Tower side balcony',(sign*5.0,-7.3,21.5),(1.0,6.6,.27),stone)
    addbox('Tower side handrail',(sign*5.48,-7.3,22.3),(.24,6.6,.19),stone)
    for a in [-10,-9,-8,-7,-6,-5,-4.6]:addbox('Tower side baluster',(sign*5.48,a,21.95),(.16,.14,.7),stone)
# Curved roof with gable ends. Tile ribs follow the actual curved slope.
def mainroof():
    w=68.2;d=22.2;z=9.75;rise=9.165
    def zz(t):return z+rise*(1-t)**1.72+.48*t**15
    # Two long curved surfaces, with hipped lower ends and vertical gable faces.
    for side in [-1,1]:
        vs=[];nx,ny=100,32
        for i in range(nx+1):
            xx=-w/2+i*w/nx
            for j in range(ny+1):
                t=j/ny;effective_x=min(w/2,32.2+1.9*t)
                actual_x=max(-effective_x,min(effective_x,xx));vs.append((actual_x,side*d/2*t,zz(t)))
        fs=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)]
        mesh('Curved main grey tile roof',vs,fs,roof)
        for xx in [v*.31 for v in range(-107,108)]:
            start=max(0,(abs(xx)-32.2)/1.9)
            pts=[(xx,side*d/2*(start+(1-start)*j/32),zz(start+(1-start)*j/32)+.065) for j in range(33)]
            curve('Main barrel tile course',pts,.088,roof)
        curve('Main raised eave',[(-34.1,side*11.1,10.23),(-32.2,side*11.1,9.99),(0,side*11.1,9.99),(32.2,side*11.1,9.99),(34.1,side*11.1,10.23)],.18,stone)
    for xx in [-32.2,32.2]:
        mesh('Main gable end',[(xx,-9.6,10),(xx,0,18.9),(xx,9.6,10)],[(0,1,2)],brick)
        curve('Main gable rake',[(xx,-11,10.23),(xx,-8,11.2),(xx,-4,14.1),(xx,0,18.92),(xx,4,14.1),(xx,8,11.2),(xx,11,10.23)],.23,stone)
    curve('Main ridge cap',[(-32.7,0,19.25),(0,0,19.1),(32.7,0,19.25)],.23,stone)
    for xx in [-32.4,32.4]:curve('Main ridge upturned end',[(xx,0,19.1),(xx,0,19.65),(xx-.28*(1 if xx>0 else -1),0,19.95)],.20,stone)
mainroof()
# Tower roof: a single curved lower roof crowned by four intersecting gables.
cy=-7.3;z=25.205
for a in [0,math.pi/2,math.pi,math.pi*1.5]:
    def tr(xx,yy,zz):return (xx*math.cos(a)-yy*math.sin(a),cy+xx*math.sin(a)+yy*math.cos(a),zz)
    vs=[];nu,nv=30,18
    for i in range(nu+1):
        xx=-6.2+i*12.4/nu
        for j in range(nv+1):
            t=j/nv;yy=-6.2+3.1*t;zz=z+.2+1.85*t*t+.23*(abs(xx)/6.2)**7;vs.append(tr(xx*(1-.4*t),yy,zz))
    fs=[(i*(nv+1)+j,(i+1)*(nv+1)+j,(i+1)*(nv+1)+j+1,i*(nv+1)+j+1) for i in range(nu) for j in range(nv)]
    mesh('Tower curved eave roof',vs,fs,roof)
    for i in range(45):
        xx=-6.18+i*12.36/44;curve('Tower eave tile ribs',[tr(xx*(1-.4*j/nv),-6.2+3.1*j/nv,z+.2+1.85*(j/nv)**2+.23*(abs(xx)/6.2)**7+.055) for j in range(nv+1)],.068,roof)
    g=[tr(-3.8,-3.7,27.0),tr(3.8,-3.7,27.0),tr(0,-3.7,30.75)];mesh('Tower triangular lattice gable',g,[(0,1,2)],lattice)
    for xx in [j*.30 for j in range(-12,13)]:
        h=3.75*(1-abs(xx)/3.8)
        curve('Gable lattice vertical',[tr(xx,-3.73,27.06),tr(xx,-3.73,27+h)],.025,wood)
    for zz in [27.3+j*.28 for j in range(12)]:
        half=3.8*(1-(zz-27)/3.75)
        curve('Gable lattice horizontal',[tr(-half,-3.74,zz),tr(half,-3.74,zz)],.025,wood)
    curve('Tower carved gable edge',[tr(-4.1,-3.77,26.95),tr(-2.2,-3.77,28.65),tr(0,-3.77,30.95),tr(2.2,-3.77,28.65),tr(4.1,-3.77,26.95)],.19,stone)
    # Tiles on both sides of each gable, sloping toward cross-roof valleys.
    for sign in [-1,1]:
        mesh('Cross-gable upper roof',[tr(0,-3.7,30.78),tr(sign*3.8,-3.7,27.0),tr(sign*3.8,0,27.0),tr(0,0,30.78)],[(0,1,2,3)],roof)
        for j in range(16):curve('Upper gable roof tile',[tr(0,-3.7+j*.245,30.85),tr(sign*3.8,-3.7+j*.245,27.05)],.063,roof)
    # Six compact corbel assemblies beneath each side, visible in the reference.
    for j in range(6):
        xx=-4.4+j*1.76
        curve('Eave corbel',[tr(xx,-4.5,24.2),tr(xx,-5.0,24.55),tr(xx,-5.65,25.1)],.12,wood)
    for xx in [-3.95,3.95]:curve('Ridge scroll ornament',[tr(xx,-3.7,27.25),tr(xx,-3.7,30.0),tr(xx*.95,-3.7,30.9),tr(xx*.90,-3.7,31.04),tr(xx*.85,-3.7,30.8)],.16,stone)
# Sculpted five-point red star on the south-facing gable.
v=[(0,cy-3.98,28.63)]
for i in range(10):
    t=math.pi/2-i*math.pi/5;r=1.55 if i%2==0 else .65;v.append((r*math.cos(t),cy-3.80,28.63+r*math.sin(t)))
mesh('Red five-point star',v,[(0,i+1,(i+1)%10+1) for i in range(10)],red)
# Vase-shaped finial, following the highest dimension on the elevation.
profile=[(30.78,.24),(31.02,.30),(31.15,.16),(31.35,.23),(31.63,.39),(31.97,.32),(32.225,.18)]
vs=[(r*math.cos(j*math.tau/20),cy+r*math.sin(j*math.tau/20),zz) for zz,r in profile for j in range(20)]
mesh('Tower vase finial',vs,[(i*20+j,i*20+(j+1)%20,(i+1)*20+(j+1)%20,(i+1)*20+j) for i in range(len(profile)-1) for j in range(20)],stone)
# Ivy: branching growth and individual leaf geometry, leaving windows readable.
leaf_batches=[([],[]) for _ in ivy]
def leaf(xx,yy,zz,r,index):
    vv,ff=leaf_batches[index];start=len(vv);roll=random.uniform(-.6,.6)
    # folded lobed leaf in a vertical plane
    shape=[(0,.85),(-.45,.45),(-.65,.14),(-.3,-.30),(0,-.55),(.35,-.22),(.63,.18),(.35,.5)]
    vv.append((xx,yy-.045,zz))
    for a,b in shape:vv.append((xx+r*(a*math.cos(roll)-b*math.sin(roll)),yy+random.uniform(-.025,.025),zz+r*(a*math.sin(roll)+b*math.cos(roll))))
    ff.extend([(start,start+j+1,start+(j+1)%8+1) for j in range(8)])
def allowed(xx,zz,opening):return not any(a-.22<xx<b+.22 and bot-.18<zz<top+.18 for a,b,bot,top in opening)
for area in ['tower','wings']:
    xmin,xmax,zmax,yy,opening=(-4.3,4.3,24.3,front-.34,topen) if area=='tower' else (-31.8,31.8,9.1,-9.76,opens)
    num=6100 if area=='tower' else 7300
    for i in range(num):
        xx=random.uniform(xmin,xmax);zz=random.uniform(.7,zmax)
        if area=='wings' and abs(xx)<5.3:continue
        density=.65+.24*math.sin(xx*2+zz*.4)+.15*math.sin(zz*1.2-xx)
        if random.random()>density or not allowed(xx,zz,opening):continue
        leaf(xx,yy-random.uniform(0,.20),zz,random.uniform(.10,.24),random.choices(range(5),weights=[30,40,20,5,5])[0])
    for j in range(25 if area=='tower' else 45):
        xx=random.uniform(xmin,xmax)
        if area=='wings' and abs(xx)<5:continue
        pts=[(xx+.28*math.sin(k*.58+j),yy+.03,k*zmax/25) for k in range(26)]
        curve('Climbing vine stem',pts,.018,wood)
for sign in [-1,1]:
    for i in range(4100):
        aa=random.uniform(-4.25,4.25);zz=random.uniform(1,24.4)
        if zz>21.7 and abs(aa)<3.45:continue
        if 17.5<zz<20.3 and abs(aa)<.85:continue
        if random.random()>.67+.2*math.sin(aa*1.8+zz*.4):continue
        idx=random.choices(range(5),weights=[30,40,20,5,5])[0];vv,ff=leaf_batches[idx];start=len(vv)
        leaf(aa,cy-5.02-random.uniform(0,.16),zz,random.uniform(.11,.25),idx)
        for j in range(start,len(vv)):
            px,py,pz=vv[j];vv[j]=(sign*(cy-py),cy+sign*px,pz)
    addbox('Tower mid side stone surround',(sign*4.99,cy,18.925),(.18,1.7,2.7),stone)
    addbox('Tower mid side sash',(sign*5.10,cy,18.925),(.10,1.4,2.35),wood)
    addbox('Tower mid side glazing',(sign*5.17,cy,18.925),(.06,1.18,2.10),glass)
    for zz in [18.4,18.925,19.45]:addbox('Tower mid side bars',(sign*5.21,cy,zz),(.08,1.3,.05),wood)
for m,(vv,ff) in zip(ivy,leaf_batches):mesh('Ivy individual leaves',vv,ff,m)
for (name,matname),(vs,fs) in batch.items():
    o=mesh(name,vs,fs,bpy.data.materials[matname])
    if name not in ['Glazing','Fine wooden mullions','Recess backing']:
        b=o.modifiers.new('Fine edge bevel','BEVEL');b.width=.025;b.segments=2;o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
# Remove trees intersecting the corrected, wider building footprint.
bpy.context.view_layer.update()
for o in list(bpy.data.collections['04 Trees and gardens'].objects):
    p=root.matrix_world.inverted()@o.location
    if abs(p.x)<34 and -13<p.y<11:bpy.data.objects.remove(o,do_unlink=True)
# Improve shared tree crowns throughout the campus (rounder, irregular surfaces).
canopies={o.data for o in bpy.data.collections['04 Trees and gardens'].objects if o.type=='MESH' and 'canopy' in o.name.lower()}
for me in canopies:
    obj=bpy.data.objects.new('temporary canopy refinement',me);s.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    sub=obj.modifiers.new('Crown subdivision','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2
    dg=bpy.context.evaluated_depsgraph_get();new=bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    for v in new.vertices:
        a=v.co.normalized();v.co=a*(.94+.10*math.sin(a.x*13+a.y*5)*math.sin(a.z*9-a.x*4))
    for f in new.polygons:f.use_smooth=True
    for o in bpy.data.collections['04 Trees and gardens'].objects:
        if o.type=='MESH' and o.data==me:o.data=new
    bpy.data.objects.remove(obj,do_unlink=True)
# Static assessment cameras: no animation in this version.
def cam(name,loc,target,lens=55,ortho=None):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=10000
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return o
def world(p):return root.matrix_world@Vector(p)
bpy.context.view_layer.update()
beauty=cam('V2 North - front three quarter',world((61,-94,43)),world((0,-3,12)),50)
frontcam=cam('V2 North - elevation inspection',world((0,-115,14)),world((0,0,14)),ortho=79)
detail=cam('V2 North - tower detail',world((14,-38,35)),world((0,-7,26)),50)
for o in bpy.data.collections['06 Typography'].objects:o.hide_render=True
s.camera=beauty;s.render.engine='CYCLES';s.cycles.samples=80;s.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.resolution_x=1800;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.view_settings.exposure=.2;s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for o in s.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.rotation_euler=(.45,-.35,-.35);o.data.energy=2.5;o.data.angle=.1
s['refinement_scope']='North Building substantially rebuilt from published plans/elevations. Other buildings still simplified massing; tree crowns refined.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NJU_Gulou_Campus_V2.blend'))
for camera,name in [(beauty,'V2_north_building.png'),(frontcam,'V2_north_elevation.png'),(detail,'V2_tower_detail.png')]:
    hidden=[]
    if camera==frontcam:
        for o in s.objects:
            if o.type not in ['CAMERA','LIGHT'] and o not in C.objects.values() and o.name!='Studio floor' and not o.hide_render:
                hidden.append(o);o.hide_render=True
    s.camera=camera;s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
    for o in hidden:o.hide_render=False
s.camera=beauty;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NJU_Gulou_Campus_V2.blend'))
json.dump({'removed_old_north_objects':len(removed),'refined_objects':len(C.objects),'ivy_leaves':sum(len(ff)//8 for vv,ff in leaf_batches),'source':root['source'],'dimensions_from_published_elevation':{'width':64.565,'eaves':9.675,'ridge':18.915,'finial':32.225},'scope':'North Building detail prototype; campus-wide architectural refinement remains pending'},open(OUT/'V2_model_notes.json','w'),indent=2)
print('REFINEMENT_COMPLETE')
