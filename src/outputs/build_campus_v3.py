"""Campus-wide architectural/landscape refinement and annotated review views.
Run in Blender 4.5 on NJU_Gulou_Campus_V2.blend. No video is generated.
"""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
random.seed(1917)
OUT=Path(__file__).resolve().parent;WORK=OUT.parent/'work';s=bpy.context.scene
F=json.load(open(OUT/'campus_footprints.json'));WORDS=json.load(open(WORK/'map_label_blocks.json',encoding='utf8'))
def collection(name):
 c=bpy.data.collections.new(name);s.collection.children.link(c);return c
ARCH=collection('09 Individually refined campus landmarks');SITE=collection('10 Landscape and street furniture');LABEL=collection('11 Verified map annotations')
def xy(p):return ((p[0]-640)*.65,(950-p[1])*.65)
def mat(n,c,r=.7):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=r;return m
BRICK=bpy.data.materials['V2 Ming city brick / 青灰明城砖'];TILE=mat('V3 Deep grey ceramic roof',(.105,.135,.13));STONE=mat('V3 Pale limestone trim',(.64,.64,.54));WOOD=mat('V3 Dark red sash',(.19,.067,.039));GLASS=mat('V3 Window glass',(.09,.17,.18),.27);PLASTER=mat('V3 Warm off-white plaster',(.72,.70,.61));PAVE=mat('V3 Warm grey paving',(.59,.60,.52));ROAD=mat('V3 Campus asphalt',(.27,.30,.28));LAWN=mat('V3 Lawn',(.32,.42,.21));METAL=mat('V3 Lamp bronze',(.10,.13,.12));RED=mat('V3 Court surface',(.43,.18,.125));WHITE=mat('V3 Court paint',(.85,.84,.71));GREEN=mat('V3 Evergreen foliage',(.19,.31,.105));TRUNK=mat('V3 Tree bark',(.23,.16,.085));DARK=mat('V3 Recess shadow',(.035,.055,.048));GOLD=mat('V3 Identification lettering',(.59,.43,.18));BASE=mat('V3 Plinth edge',(.12,.18,.16))
def textured(m,scale=5,strength=.15):
 n=m.node_tree.nodes;l=m.node_tree.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=.08;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
for m in [TILE,PAVE,ROAD,LAWN,STONE,PLASTER,TRUNK]:textured(m,18 if m==TILE else 7)
def mesh(n,vs,fs,m,c=ARCH,parent=None):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);c.objects.link(o);o.data.materials.append(m);o.parent=parent;return o
def path(n,pts,r,m,c=ARCH,parent=None):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=1;cu.use_fill_caps=True;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(n,cu);c.objects.link(o);o.parent=parent;cu.materials.append(m);return o
def prism(n,pts,z,h,m,c=SITE):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='2D';cu.resolution_u=1;cu.fill_mode='BOTH';cu.extrude=h/2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,0,1)
 sp.use_cyclic_u=True;o=bpy.data.objects.new(n,cu);c.objects.link(o);o.location.z=z+h/2;cu.materials.append(m);return o
def bboxcenter(o):
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];return sum(pts,Vector())/8
def nearfeature(o,idx,pad=0):
 q=bboxcenter(o);a,b,c,d=F[idx]['bounds'];u=q.x/.65+640;v=950-q.y/.65;return a-pad<u<c+pad and b-pad<v<d+pad
REPLACED={69,70,71,81,89,87,194,212}
for colname in ['02 Map-derived buildings','03 Heritage landmarks']:
 for o in list(bpy.data.collections[colname].objects):
  if o.name.startswith('Batched facade') or any(nearfeature(o,i,1.7) for i in REPLACED):bpy.data.objects.remove(o,do_unlink=True)
# V2 north detail is preserved. All new landmarks are editable semantic assemblies.
class Building:
 def __init__(self,name,u,v,angle=0,source=''):
  self.name=name;self.root=bpy.data.objects.new(name,None);ARCH.objects.link(self.root);self.root.location=(*xy((u,v)),.65);self.root.rotation_euler.z=angle;self.root['source']=source;self.root['accuracy']='photo/plan-informed exterior; approximate scale';self.batch={}
 def box(self,name,p,dim,m):
  vs,fs=self.batch.setdefault((name,m.name),([],[]));i=len(vs);x,y,z=p;w,d,h=[v/2 for v in dim];vs.extend([(x+a*w,y+b*d,z+c*h) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]);fs.extend([tuple(i+j for j in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 def line(self,name,pts,r,m):return path(self.name+' / '+name,pts,r,m,parent=self.root)
 def rod(self,name,a,b,r,m):
  a,b=Vector(a),Vector(b);t=(b-a).normalized();side=t.cross(Vector((0,0,1)))
  if side.length<.01:side=t.cross(Vector((0,1,0)))
  side.normalize();up=t.cross(side).normalized();vs,fs=self.batch.setdefault((name,m.name),([],[]));i=len(vs)
  vs.extend([tuple(p+side*xx*r+up*yy*r) for p in [a,b] for xx,yy in [(-1,-1),(1,-1),(1,1),(-1,1)]]);fs.extend([tuple(i+j for j in face) for face in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]])
 def win(self,x,y,z,w=1.25,h=2.1):
  self.box('Window reveals',(x,y+.08,z),(w+.18,.12,h+.2),DARK);self.box('Glazing',(x,y-.005,z),(w,.06,h),GLASS)
  for dx in [-w/2,0,w/2]:self.box('Wooden sash',(x+dx,y-.06,z),(.055,.15,h+.1),WOOD)
  for dz in [-h/2,0,h/2]:self.box('Wooden sash',(x,y-.06,z+dz),(w+.08,.15,.065),WOOD)
  self.box('Stone lintels',(x,y-.09,z+h/2+.12),(w+.35,.31,.18),STONE);self.box('Stone sills',(x,y-.16,z-h/2-.12),(w+.32,.44,.16),STONE)
 def shell(self,w,d,h,cx=0,cy=0,wallmat=BRICK):
  self.box('Masonry mass',(cx,cy,h/2),(w,d,h),wallmat)
  for z,hh in [(.4,.6),(4.2,.23),(h-.25,.26)]:self.box('Stone courses',(cx,cy,z),(w+.25,d+.25,hh),STONE)
 def rows(self,w,d,levels=2,spacing=2.6,cx=0,cy=0):
  n=int((w-3)/spacing)
  for j in range(n):
   x=cx+(j-(n-1)/2)*spacing
   for k in range(levels):self.win(x,cy-d/2-.10,2.25+k*3.65)
  # Rear windows face the opposite direction; separate panels and timber grid.
  for j in range(n):
   x=cx+(j-(n-1)/2)*spacing
   for k in range(levels):
    z=2.25+k*3.65;self.box('Rear glazing',(x,cy+d/2+.10,z),(1.25,.12,2.1),GLASS)
    for dx in [-.67,0,.67]:self.box('Rear sash',(x+dx,cy+d/2+.18,z),(.06,.11,2.2),WOOD)
    self.box('Rear sill',(x,cy+d/2+.22,z-1.17),(1.55,.35,.16),STONE)
 def doorway(self,y,z=0,w=2.2):
  self.box('Entrance dark door',(0,y-.11,z+1.7),(w,.2,3.4),WOOD)
  for x in [-w/2-.22,w/2+.22]:self.box('Entrance stone surround',(x,y-.22,z+1.9),(.34,.6,3.9),STONE)
  self.box('Entrance lintel',(0,y-.22,z+3.9),(w+1,.65,.35),STONE)
  for j in range(6):self.box('Entrance steps',(0,y-.65-j*.32,z+.5-j*.075),(w+1+j*.2,.44,.17),STONE)
 def roof(self,w,d,z,rise,cx=0,cy=0,angle=0,tiles=True):
  def tr(x,y,z):return (cx+x*math.cos(angle)-y*math.sin(angle),cy+x*math.sin(angle)+y*math.cos(angle),z)
  def height(t):return z+rise*(1-t)**1.65+.34*t**12
  for sign in [-1,1]:
   vs=[];nx,ny=12,20
   for i in range(nx+1):
    for j in range(ny+1):
     t=j/ny;x=(i/nx-.5)*(w+2*t);vs.append(tr(x,sign*(d/2+1)*t,height(t)))
   fs=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)];mesh(self.name+' / Curved tiled roof',vs,fs,TILE,parent=self.root)
   if tiles:
    for i in range(int(w/.45)+1):
     xx=-w/2+i*w/int(w/.45);self.line('Barrel tile ribs',[tr(xx,sign*(d/2+1)*t/20,height(t/20)+.04) for t in range(21)],.057,TILE)
   self.line('Curved eave',[tr(-w/2-1,sign*(d/2+1),z+.4),tr(-w/2+2,sign*(d/2+1),z+.2),tr(w/2-2,sign*(d/2+1),z+.2),tr(w/2+1,sign*(d/2+1),z+.4)],.12,TILE)
  for xx in [-w/2,w/2]:
   mesh(self.name+' / Gable brickwork',[tr(xx,-d/2,z),tr(xx,0,z+rise),tr(xx,d/2,z)],[(0,1,2)],BRICK,parent=self.root)
   self.line('Gable carved rake',[tr(xx,-d/2-1,z+.34),tr(xx,-d/4,z+rise*.32),tr(xx,0,z+rise+.10),tr(xx,d/4,z+rise*.32),tr(xx,d/2+1,z+.34)],.16,TILE)
  self.line('Ridge cap',[tr(-w/2,0,z+rise+.28),tr(0,0,z+rise+.12),tr(w/2,0,z+rise+.28)],.17,TILE)
  for xx in [-w/2,w/2]:self.line('Ridge finials',[tr(xx,0,z+rise+.1),tr(xx,0,z+rise+.8),tr(xx-.28*(1 if xx>0 else -1),0,z+rise+1.0)],.14,TILE)
 def finish(self):
  for (name,m),(vs,fs) in self.batch.items():
   o=mesh(self.name+' / '+name,vs,fs,bpy.data.materials[m],parent=self.root)
   if name not in ['Glazing','Rear glazing','Wooden sash','Rear sash']:
    mod=o.modifiers.new('Subtle edge rounding','BEVEL');mod.width=.035;mod.segments=1
  return self.root
sources={n:f'https://dawww.nju.edu.cn/info/1201/{code}.htm' for n,code in [('east','10671'),('west','10651'),('auditorium','10691'),('museum','10631'),('chapel','10681'),('southwest','10581'),('northeast','10621')]}
for name,u,v,rot,kind in [('东大楼',973,659,-math.pi/2+.12,'east'),('西大楼',833,675,math.pi/2+.12,'west')]:
 b=Building(name,u,v,rot,sources[kind]);b.shell(45,15,9.6);b.rows(45,15,2,2.4);b.doorway(-7.55)
 b.roof(46,16,9.7,5.4);b.roof(15,16.4,9.8,8.9)
 b.shell(15,11,10,0,10.8);b.roof(16,11.5,10.1,8.1,0,10.8)
 for x in [-4.8,-2.4,0,2.4,4.8]:b.win(x,-8.30,8,1.45,2.0)
 b.finish()
b=Building('大礼堂',838,743,math.pi/2+.12,sources['auditorium']);b.shell(24,34,6.4);b.shell(14,32,11.2);b.roof(34,15.5,11.3,6.2,angle=math.pi/2)
for x in [-9.6,9.6]:
 b.roof(31,7,6.4,2.4,x,0,math.pi/2)
 b.shell(5.8,6.5,8.8,x,-14.5);b.roof(7,6.5,8.9,2.9,x,-14.5,math.pi/2)
for x in [-4.3,-2.15,0,2.15,4.3]:b.win(x,-16.1,9.0,1.65,2.0)
for x in [-3.4,0,3.4]:b.box('Three timber front doors',(x,-17.15,2.4),(2.5,.23,4.1),WOOD)
b.roof(12,4.8,5.9,1.6,0,-17);b.doorway(-17.3,w=9.6)
for x in [-7.03,7.03]:
 for y in range(-12,14,3):b.box('Clerestory windows',(x,y,9.1),(.12,1.65,2.2),GLASS)
b.finish()
b=Building('校史博物馆 · 原金陵大学图书馆',942,950,math.pi+.12,sources['museum']);b.shell(46,13,10.2,wallmat=PLASTER);b.rows(46,13,2,2.4);b.roof(47,14,10.3,4.8)
b.shell(13,8,13.2,0,-3.0,PLASTER);b.roof(14,10,13.3,5.4,0,-3.0);b.roof(12,3.5,7.6,0.9,0,-8.1);b.doorway(-8,w=3.0)
for x in [-5,-2.5,0,2.5,5]:b.box('Museum red columns',(x,-7.3,9.0),(.30,.35,4.4),WOOD)
for x in [-20,-16,-12,-8,8,12,16,20]:b.win(x,-6.65,7.2,3.1,2.35)
b.shell(11,22,13.0,0,16,PLASTER)
for y in range(7,26,3):
 for x in [-5.6,5.6]:b.box('Book stack glazing',(x,y,8),(.16,1.7,4.6),GLASS)
b.finish()
b=Building('小礼堂',855,879,math.pi/2+.12,sources['chapel']);b.shell(9,10,5.2);b.roof(10.5,9.2,5.3,3.05,angle=math.pi/2)
# Arched door and circular side windows with stone surrounds.
pts=[(-1.0,-5.15,.6),(-1,-5.15,3.1)]+[(math.cos(t*math.pi/24),-5.15,3.1+math.sin(t*math.pi/24)) for t in range(24,-1,-1)]+[(1,-5.15,.6)]
mesh('小礼堂 / arched timber door',pts,[tuple(range(len(pts)))],WOOD,parent=b.root);b.line('Arch stone moulding',pts,.14,STONE)
for xx in [-2.8,2.8]:
 ring=[(xx+.55*math.cos(t*math.tau/40),-5.17,3.15+.55*math.sin(t*math.tau/40)) for t in range(41)];b.line('Round window stone ring',ring,.095,STONE);mesh('小礼堂 / round window',ring,[tuple(range(40))],GLASS,parent=b.root)
for j in range(7):b.box('Wide stone stair',(0,-5.5-j*.34,.56-j*.07),(4.6,.44,.17),STONE)
b.finish()
b=Building('西南楼',607,863,math.pi/2+.10,sources['southwest']);b.shell(74,11,12.4,0,-8,PLASTER);b.rows(74,11,3,2.55,0,-8);b.roof(75,12,12.5,5.3,0,-8)
for x in [-30,30]:
 b.shell(13.5,45,12.4,x,0,PLASTER);b.roof(46,14.5,12.5,4.8,x,0,math.pi/2);b.rows(13.5,45,3,2.45,x,0)
b.doorway(-13.6,z=.5,w=3.8);b.finish()
b=Building('东北楼',972,556,math.pi/2+.12,sources['northeast']);b.shell(26,13,12.4,wallmat=PLASTER);b.rows(26,13,3,2.45);b.roof(27,14,12.5,4.0);b.doorway(-6.6);b.finish()
print('Individual landmarks built',flush=True)

# Replace the large empty rectangular board with a campus-shaped presentation base.
outline_uv=[(62,306),(657,319),(688,412),(789,438),(815,532),(979,436),(1030,700),(1087,1054),(1147,1297),(1217,1606),(790,1630),(778,1355),(684,1264),(665,1119),(535,1128),(523,1037),(356,1038),(254,811),(63,811)]
outline=[xy(p) for p in outline_uv]
for o in list(bpy.data.collections['01 Terrain and paths'].objects):
 if o.name!='Studio floor' and not o.name.startswith('Garden '):bpy.data.objects.remove(o,do_unlink=True)
prism('Campus-shaped presentation plinth',outline,-6.3,6.2,BASE);prism('Continuous campus paving',outline,-.1,.34,PAVE)
path('Plinth perimeter reveal',[(a,b,-.8) for a,b in outline]+[(*outline[0],-.8)],.13,STONE,SITE)
def inside(p,polygon):
 x,y=p;v=False
 for a,b in zip(polygon,polygon[1:]+polygon[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
 return v
def ribbon(name,uv,w,m=ROAD):
 pts=[Vector((*xy(p),.29)) for p in uv];vs=[]
 for i,p in enumerate(pts):
  direction=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();perp=Vector((-direction.y,direction.x,0));vs.extend([tuple(p+perp*w/2),tuple(p-perp*w/2)])
 mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],m,SITE)
 for side in [0,1]:path(name+' / curb',[(vs[i*2+side][0],vs[i*2+side][1],.39) for i in range(len(pts))],.075,STONE,SITE)
 return pts
roads=[('汉口路',[(533,1107),(843,1080),(1084,1057)],10),('平仓巷',[(376,329),(366,454),(399,636),(421,779)],6),('金银街',[(87,494),(350,498)],5),('北园西路',[(369,454),(534,451),(554,753)],5),('西南路',[(648,798),(671,1054)],5),('中大路',[(759,750),(785,812),(817,954),(841,1062)],6),('金大路',[(899,622),(914,731),(930,848),(949,1035)],4.5),('东西通道',[(277,794),(525,778),(755,745),(995,708)],5.5),('两江路',[(644,820),(931,783)],4),('三江路',[(670,896),(949,860)],4),('书苑路',[(688,1060),(1065,1025)],4),('南园中路',[(850,1124),(867,1230),(907,1371),(957,1566)],5),('南园东路',[(1008,1104),(1042,1276),(1094,1544)],4.5),('广州路入口',[(810,1607),(1191,1583)],5)]
for name,p,w in roads:ribbon(name,p,w)
for v in [1165,1223,1290,1371,1455,1545]:
 left=705+(v-1165)*.27;right=1090+(v-1165)*.23;ribbon('南园支路',[(left,v),(right,v-23)],3.5)
# Central heritage lawn is deliberately open and crossed by light paths.
for p in [[(857,624),(867,710)],[(933,616),(944,699)],[(858,666),(938,656)]]:ribbon('历史建筑区步道',p,2.1,STONE)

# Rebuild ordinary facades: variable proportions, projecting sills, entrance markers,
# dormitory railings and rooftop plant instead of one repeated floating window mesh.
NEWM=[mat('V3 Facade tone '+str(i),c) for i,c in enumerate([(.68,.66,.57),(.57,.58,.52),(.73,.70,.61),(.48,.40,.32),(.64,.62,.54)])]
annotations=[]
def label(name,u,v,z,kind,detail,source='',priority=2):
 pos=[*xy((u,v)),z];e=bpy.data.objects.new('标注 / '+name,None);LABEL.objects.link(e);e.location=pos;e.empty_display_type='SPHERE';e.empty_display_size=.65;e['label']=name;e['category']=kind;e['description']=detail;e['source']=source
 annotations.append({'name':name,'position':pos,'category':kind,'description':detail,'source':source,'priority':priority})
for i,f in enumerate(F):
 k=f['kind']
 if k in ['lawn','grass','sport'] or i in REPLACED or i==72:continue
 a,b,c,d=f['bounds'];u=(a+c)/2;v=(b+d)/2
 candidates=[q['text'] for q in WORDS if a<(q['bounds'][0]+q['bounds'][2])/2<c and b<(q['bounds'][1]+q['bounds'][3])/2<d and 2<=len(q['text'])<=9 and not any(t in q['text'] for t in ['路','雕像','纪念','地下','警卫'])]
 name=candidates[0] if candidates else {'academic':'教学科研楼','historic':'历史建筑','dorm':'学生宿舍','teaching':'教学楼','service':'生活服务楼','admin':'行政楼'}[k]+' %03d'%i
 height={'historic':11,'academic':17.5,'dorm':18,'service':9,'teaching':16,'admin':14}[k]
 if u<530 and v<750:height+=6
 # Recover the original curve height, avoiding speculative changes to massing.
 for o in bpy.data.collections['02 Map-derived buildings'].objects:
  if o.type=='CURVE' and nearfeature(o,i) and 'height_m' in o:height=float(o['height_m']);o.name=name+' / 主体';o['map_name']=name;o.data.materials.clear();o.data.materials.append(NEWM[(i%3) if k!='dorm' else 3]);break
 modern=Building(name,u,v)
 # Geometry is entered in world space for irregular map footprints.
 modern.root.location=(0,0,0)
 for loop in f['loops']:
  pts=[Vector((*xy(p),0)) for p in loop]
  area=sum(p.x*q.y-p.y*q.x for p,q in zip(pts,pts[1:]+pts[:1]))
  for p,q in zip(pts,pts[1:]+pts[:1]):
   edge=q-p;length=edge.length
   if length<3.3:continue
   t=edge.normalized();n=Vector((t.y,-t.x,0))*(1 if area>0 else -1);count=max(1,int(length/(3.05 if k=='dorm' else 3.8)));floors=max(1,int(height/3.6))
   for j in range(count):
    center=p+edge*((j+.5)/count)+n*.10;ww=min(1.7,length/count*.55);hh=1.7 if k=='dorm' else 2.0
    for floor in range(floors):
     z=2.15+floor*3.5
     if z+hh/2>height:continue
     # Rectangular quads oriented to the actual map facade.
     verts=[tuple(center-t*ww/2+Vector((0,0,z-hh/2))),tuple(center+t*ww/2+Vector((0,0,z-hh/2))),tuple(center+t*ww/2+Vector((0,0,z+hh/2))),tuple(center-t*ww/2+Vector((0,0,z+hh/2)))]
     vv,ff=modern.batch.setdefault(('Facade glazing',GLASS.name),([],[]));idx=len(vv);vv.extend(verts);ff.append((idx,idx+1,idx+2,idx+3))
     for dz in [-hh/2,hh/2]:modern.rod('Sills',center-t*(ww/2+.1)+Vector((0,0,z+dz)),center+t*(ww/2+.1)+Vector((0,0,z+dz)),.07,STONE)
     if k=='dorm' and floor>0:
      front=center+n*.55;modern.rod('Balcony rails',front-t*(ww/2+.2)+Vector((0,0,z-.1)),front+t*(ww/2+.2)+Vector((0,0,z-.1)),.035,METAL)
   # Horizontal facade banding on selected academic buildings.
   if k in ['academic','teaching']:
    for z in [3.9,height-.35]:modern.rod('Facade bands',p+n*.08+Vector((0,0,z)),q+n*.08+Vector((0,0,z)),.10,STONE)
 # HVAC and roof access huts, restricted to small footprints inside the map polygon.
 loop=f['loops'][0]
 for j in range(3 if k in ['academic','teaching'] else 1):
  pu=u+(j-1)*3;pv=v
  if inside((pu,pv),loop):
   xx,yy=xy((pu,pv));modern.box('Roof services',(xx,yy,height+1.6),(1.8,1.2,1.0),STONE)
   for sl in [-.45,0,.45]:modern.box('Ventilator grille',(xx+sl,yy,height+2.13),(.13,1.0,.05),METAL)
 modern.finish()
 # Small historic residences have tiled roofs; preserve their map footprint.
 if k=='historic' and c-a<65 and d-b<85:
  w=(c-a)*.58;depth=(d-b)*.58;xx,yy=xy((u,v));old=Building(name+' / 瓦顶',u,v)
  if depth>w:old.roof(depth,w,height+1.1,3.8,angle=math.pi/2+.12)
  else:old.roof(w,depth,height+1.1,3.8,angle=.12)
  old.finish()
 if candidates and not any(t in name for t in ['小楼','旧居']):
  label(name,u,v,height+2,'生活' if k in ['dorm','service'] else '建筑','名称与位置依据2024年官方地图；普通建筑外观为简化重建。',priority=3)
print('Campus facades differentiated',flush=True)

# Branching tree assets with many small crown clusters, shared across the campus.
oldtrees=[]
for o in list(bpy.data.collections['04 Trees and gardens'].objects):
 if o.name.startswith('Tree trunk'):oldtrees.append((o.location.x,o.location.y,max(5,o.scale.z/.6)))
 bpy.data.objects.remove(o,do_unlink=True)
TREE=collection('12 Branching trees and planting')
foliage=[mat('V3 Leaf palette '+str(i),c) for i,c in enumerate([(.20,.32,.10),(.28,.39,.15),(.37,.44,.19),(.13,.25,.08),(.43,.40,.16),(.25,.36,.18)])]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1);tmp=bpy.context.object;iv=[v.co.copy() for v in tmp.data.vertices];iff=[tuple(p.vertices) for p in tmp.data.polygons];bpy.data.objects.remove(tmp,do_unlink=True)
templates=[]
for variant in range(9):
 vs=[];fs=[];mids=[]
 def cylinder(a,b,r1,r2):
  a,b=Vector(a),Vector(b);t=(b-a).normalized();u=t.cross(Vector((0,1,0))).normalized();v=t.cross(u).normalized();idx=len(vs)
  for center,r in [(a,r1),(b,r2)]:
   for j in range(6):vs.append(tuple(center+r*(math.cos(j*math.tau/6)*u+math.sin(j*math.tau/6)*v)))
  for j in range(6):fs.append((idx+j,idx+(j+1)%6,idx+6+(j+1)%6,idx+6+j));mids.append(0)
 cylinder((0,0,0),(.015,0,.77),.019,.006)
 for j in range(10):
  a=j*2.399;z=.38+j*.032;end=(math.cos(a)*.23,math.sin(a)*.23,z+.20);cylinder((0,0,z),end,.009,.0025)
 for j in range(110):
  a=random.uniform(0,math.tau);r=math.sqrt(random.random())*.31;zz=random.uniform(.50,.98)
  if variant%3==0:r*=max(.12,(1.13-zz)/.55)
  else:r*=max(.2,math.sqrt(max(.01,1-((zz-.75)/.28)**2)))
  center=Vector((r*math.cos(a),r*math.sin(a),zz));size=random.uniform(.048,.083);idx=len(vs)
  for vert in iv:vs.append(tuple(center+Vector((vert.x*size,vert.y*size,vert.z*size*.85))))
  fs.extend([tuple(idx+i for i in f) for f in iff]);mids.extend([1+random.randrange(3)]*len(iff))
 me=bpy.data.meshes.new('Tree species variant %02d'%variant);me.from_pydata(vs,[],fs);me.materials.append(TRUNK)
 for k in range(3):me.materials.append(foliage[(variant+k)%len(foliage)])
 for p,mi in zip(me.polygons,mids):p.material_index=mi;p.use_smooth=True
 templates.append(me)
def plant(x,y,h):
 u=x/.65+640;v=950-y/.65
 if not inside((u,v),outline_uv):return
 if 126<x<202 and 215<y<244:return
 for i in REPLACED:
  a,b,c,d=F[i]['bounds']
  if a-2<u<c+2 and b-2<v<d+2:return
 o=bpy.data.objects.new('校园乔木',random.choice(templates));TREE.objects.link(o);o.location=(x,y,.35);o.scale=(h,h,h);o.rotation_euler.z=random.uniform(0,math.tau)
for tx,ty,h in oldtrees:plant(tx,ty,h*random.uniform(1.1,1.45))
# Add northern/western avenue planting and generous but non-obstructing south rows.
for name,uv,w in roads:
 for a,b in zip(uv,uv[1:]):
  pa,pb=Vector(xy(a)),Vector(xy(b));length=(pb-pa).length;t=(pb-pa).normalized();n=Vector((-t.y,t.x))
  for j in range(int(length/12)):
   pos=pa+t*(j*12+5)
   for sign in [-1,1]:
    p=pos+n*sign*(w/2+2.2);u=p.x/.65+640;v=950-p.y/.65
    if any(f['kind'] not in ['lawn','grass','sport'] and f['bounds'][0]-2<u<f['bounds'][2]+2 and f['bounds'][1]-2<v<f['bounds'][3]+2 for f in F):continue
    plant(p.x,p.y,random.uniform(8.2,12.5))

# Benches, lights, small hedges and paving joints at human scale.
furniture=Building('道路及庭院设施',640,950);furniture.root.location=(0,0,0)
for name,uv,w in roads:
 for a,b in zip(uv,uv[1:]):
  pa,pb=Vector(xy(a)),Vector(xy(b));t=(pb-pa).normalized();n=Vector((-t.y,t.x));length=(pb-pa).length
  for j in range(int(length/24)):
   p=pa+t*(j*24+8)+n*(w/2+.8)
   furniture.rod('灯杆',(p.x,p.y,.4),(p.x,p.y,4.2),.055,METAL);furniture.box('灯罩',(p.x,p.y,4.25),(.42,.42,.22),STONE)
  for j in range(int(length/40)):
   p=pa+t*(j*40+16)-n*(w/2+1.6)
   for k in [-.23,0,.23]:furniture.rod('长椅木板',(p.x-t.x,p.y-t.y+k,.92),(p.x+t.x,p.y+t.y+k,.92),.09,WOOD)
   for sign in [-1,1]:q=p+t*sign*.72;furniture.rod('长椅支脚',(q.x,q.y,.35),(q.x,q.y,.90),.065,METAL)
furniture.finish()
# Stadium seating, safety fences and detailed court markings.
sport=Building('苏浙运动场设施',630,617,.105)
for k in range(5):sport.box('西看台台阶',(-40-k*.7,0,.6+k*.30),(1.1,68,.45),STONE)
for y in range(-42,45,4):
 for x in [-37.3,37.3]:sport.rod('跑道围栏柱',(x,y,.5),(x,y,2.0),.04,METAL)
for x in [-37.3,37.3]:sport.rod('跑道围栏横杆',(x,-44,1.5),(x,44,1.5),.035,METAL)
for x in [-45,45]:
 for y in [-46,46]:sport.rod('球场灯塔',(x,y,0),(x,y,14),.13,METAL);sport.box('球场灯架',(x,y,14),(2.2,.6,.4),STONE)
sport.finish()
for i,f in enumerate(F):
 if f['kind']!='sport':continue
 a,b,c,d=f['bounds'];u=(a+c)/2;v=(b+d)/2
 if (d-b)<20 or (c-a)>42 or v<490:continue
 if not (u<570 or u>700):continue
 x,y=xy((u,v));w=(c-a)*.65*.85;h=(d-b)*.65*.88
 path('球场边线',[(x-w/2,y-h/2,.8),(x+w/2,y-h/2,.8),(x+w/2,y+h/2,.8),(x-w/2,y+h/2,.8),(x-w/2,y-h/2,.8)],.065,WHITE,SITE)
 path('球场中线',[(x-w/2,y,.8),(x+w/2,y,.8)],.06,WHITE,SITE)

# Explicit, source-backed points of interest, overriding ambiguous automatic names.
verified=[
 ('北大楼',891,597,33,'历史建筑','依据南立面与东立面图重建五层塔楼、十字形塔顶、红星、窗格及假阳台。','https://dawww.nju.edu.cn/info/1201/10711.htm',1),
 ('东大楼',973,659,20,'历史建筑','科学馆；独立建模中部抬高屋面、后侧突出体量与石门罩。',sources['east'],1),
 ('西大楼',833,675,20,'历史建筑','原裴义理堂；依据图纸与照片补建屋面、窗带和入口。',sources['west'],1),
 ('大礼堂',838,743,20,'历史建筑','高侧窗、主屋面与低侧廊层次，东向入口及多层檐口。',sources['auditorium'],1),
 ('校史博物馆',942,950,21,'历史建筑','原金陵大学图书馆；重建中部门厅、挑檐及后侧书库体量。',sources['museum'],1),
 ('小礼堂',855,879,10,'历史建筑','独立小体量，增加石砌拱门、圆窗和入口台阶。',sources['chapel'],2),
 ('西南楼',607,863,19,'历史建筑','1954年建筑；依据H形平面及立面照片建模，补三层窗带。',sources['southwest'],1),
 ('东北楼',972,556,18,'历史建筑','三层楼体和坡屋顶，参考档案照片。',sources['northeast'],2),
 ('苏浙运动场',630,617,1,'体育','跑道、足球场、球门、看台、围栏与灯杆；依据校园地图。','',1),
 ('体育馆',709,445,14,'体育','位置依据2024年校园地图，外观为简化体量。','',2),
 ('吕志和游泳馆',773,496,14,'体育','位置依据2024年校园地图，外观为简化体量。','',2),
 ('汉口路校门',841,1063,10,'校门','根据官方正门照片建模。','https://nh.nju.edu.cn/xysh/xyfg/glxq/1.htm',1),
 ('北园',761,921,1,'分区','鼓楼校区北园：历史建筑、教学科研与运动场。','',0),
 ('南园',949,1345,1,'分区','汉口路以南的生活片区。','',0),
 ('汉口路',697,1093,1,'道路','连接与分隔南北园的城市道路。','',1),
 ('中大路',810,944,1,'道路','北园南部的校园轴线。','',2),
 ('金大路',917,766,1,'道路','历史建筑区南北向道路。','',2),
 ('平仓巷',388,601,1,'道路','西侧建筑片区的南北通道。','',2),
 ('南园篮球场',977,1566,2,'体育','南园南部篮球场。','',2),
 ('图书馆',951,1026,20,'建筑','依据2024年地图标注，位于校史博物馆南侧。','',2),
]
vernames={r[0] for r in verified};annotations=[a for a in annotations if a['name'] not in vernames]
for row in verified:label(*row)
for a in annotations:
 if not a['source']:a['source']='https://zcc.nju.edu.cn/dzdt/glxqdt/index.html'
# One annotation per unique name; retain the highest-priority entry.
unique={}
for a in sorted(annotations,key=lambda a:a['priority']):unique.setdefault(a['name'],a)
annotations=list(unique.values());json.dump(annotations,open(OUT/'campus_annotations.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
font_candidates=[Path('C:/Windows/Fonts/msyh.ttc'),Path('/usr/share/fonts/truetype/msttcorefonts/msttcorefonts.ttf'),Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')]
font_path=next((p for p in font_candidates if p.exists()),None)
font=bpy.data.fonts.load(str(font_path)) if font_path else bpy.data.fonts.get('Bfont')
for a in annotations:
 cu=bpy.data.curves.new(a['name'],'FONT');cu.body=a['name'];cu.font=font;cu.size=3.2 if a['priority']>0 else 7;cu.align_x='CENTER';cu.extrude=.015;o=bpy.data.objects.new('地面标注 / '+a['name'],cu);LABEL.objects.link(o);o.location=(a['position'][0],a['position'][1]-3,.8);cu.materials.append(BASE);o.hide_render=True
print('Landscape and verified annotations ready',len(annotations),flush=True)

# Six static review cameras. Annotations are projected for readable 2D labels.
def camera(name,loc,target,scale):
 data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;data.clip_end=10000;o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
views=[
 ('overview',camera('V3 全校鸟瞰',(920,-1350,1570),(35,-8,0),1260),['北大楼','西南楼','苏浙运动场','校史博物馆','汉口路','南园','北园','汉口路校门']),
 ('heritage',camera('V3 历史建筑群',(400,10,350),(125,177,0),385),['北大楼','东大楼','西大楼','大礼堂','苏浙运动场','金大路']),
 ('museum',camera('V3 博物馆与图书馆',(400,240,245),(193,-8,0),235),['校史博物馆','图书馆','小礼堂','汉口路校门']),
 ('south',camera('V3 南园生活区',(450,-685,570),(215,-255,0),475),['南园','南园篮球场','南园8舍','南园1舍','南园6舍','南园14舍']),
 ('plan',camera('V3 全校标注总图',(25,-13,2000),(25,-13,0),970),[a['name'] for a in annotations if a['priority']<3]),
 ('auditorium',camera('V3 大礼堂近景',(244,56,91),(129,131,8),115),['大礼堂']),
]
s.render.engine='CYCLES';s.cycles.samples=56;s.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.resolution_x=2000;s.render.resolution_y=1600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.exposure=.3
s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
for o in s.objects:
 if o.type=='LIGHT' and o.data.type=='SUN':o.rotation_euler=(.42,-.38,-.36);o.data.energy=2.3;o.data.angle=.14
for o in bpy.data.collections['06 Typography'].objects:o.hide_render=True
bpy.context.view_layer.update();s.camera=views[0][1];s['model_stage']='Campus-wide detailed presentation model; static review, no video';s['annotation_count']=len(annotations)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NJU_Gulou_Campus_V3.blend'))
projected={}
for slug,cam,names in views:
 s.camera=cam;s.render.resolution_x=2000;s.render.resolution_y=1800 if slug in ['overview','plan'] else 1400
 projected[slug]={'size':[s.render.resolution_x,s.render.resolution_y],'labels':[]}
 for a in annotations:
  if a['name'] not in names:continue
  p=world_to_camera_view(s,cam,Vector(a['position']));projected[slug]['labels'].append({'name':a['name'],'x':p.x,'y':1-p.y,'depth':p.z,'category':a['category']})
 s.render.filepath=str(OUT/('V3_'+slug+'_clean.png'));bpy.ops.render.render(write_still=True)
json.dump(projected,open(OUT/'V3_projected_labels.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
s.camera=views[0][1];s.render.resolution_x=2000;s.render.resolution_y=1800;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'NJU_Gulou_Campus_V3.blend'))
json.dump({'refined_landmarks':8,'annotations':len(annotations),'tree_instances':len(TREE.objects),'objects':len(s.objects),'static_views':6,'video_created':False},open(OUT/'V3_stats.json','w'),indent=2)
print('V3_COMPLETE',flush=True)
