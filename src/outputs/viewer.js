import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const $=s=>document.querySelector(s),annotations=JSON.parse($('#annotations').textContent);
const scene=new THREE.Scene();scene.background=new THREE.Color('#e6e9e3');
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.22;document.querySelector('#canvas').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-600,600,600,-600,.1,10000),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.13;controls.minZoom=.5;controls.maxZoom=24;controls.maxPolarAngle=Math.PI*.48;
scene.add(new THREE.HemisphereLight(0xf5f8ed,0x627063,2));const sun=new THREE.DirectionalLight(0xfff2d8,3.3);sun.position.set(-350,800,420);scene.add(sun);
renderer.shadowMap.enabled=false;renderer.shadowMap.type=THREE.PCFSoftShadowMap;sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-650,right:650,top:650,bottom:-650,near:1,far:2000});sun.shadow.bias=-.00005;sun.shadow.normalBias=.25;
const V=(x,y,z)=>new THREE.Vector3(x,z,-y),views={overview:{p:V(920,-1350,1570),t:V(35,-8,0),scale:1260},heritage:{p:V(400,10,350),t:V(125,177,0),scale:385},south:{p:V(450,-685,570),t:V(215,-255,0),scale:475},plan:{p:V(25,-13,2000),t:V(25,-13,0),scale:970}};
let scale=1260,showLabels=true,ready=false;
function resize(){const aspect=innerWidth/innerHeight;camera.left=-scale*aspect/2;camera.right=scale*aspect/2;camera.top=scale/2;camera.bottom=-scale/2;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
function view(id){const v=views[id];camera.position.copy(v.p);controls.target.copy(v.t);scale=v.scale;camera.zoom=1;resize();controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===id));window.__campusView=id;}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));view('overview');addEventListener('resize',resize);
const labels=annotations.map(a=>{const el=document.createElement('button');el.className='map-label '+(a.priority===0?'region':'');el.textContent=a.name;el.onclick=()=>focus(a);$('#labels').append(el);return{a,el,p:V(...a.position)};});
function focus(a){const p=V(...a.position);scale=140;camera.zoom=1;controls.target.copy(p);camera.position.copy(p).add(new THREE.Vector3(150,125,170));resize();$('#detail').hidden=false;$('#detail-name').textContent=a.name;$('#detail-category').textContent=a.category;$('#detail-description').textContent=a.description;$('#source').href=a.source;$('#search').value=a.name;window.__campusFocus=a.name;}
$('#close').onclick=()=>$('#detail').hidden=true;
$('#toggle').onclick=()=>{showLabels=!showLabels;$('#toggle').textContent=showLabels?'隐藏标注':'显示标注';$('#toggle').setAttribute('aria-pressed',String(showLabels));};
const names=$('#names');for(const a of annotations){const op=document.createElement('option');op.value=a.name;names.append(op);}
$('#search').onchange=()=>{const a=annotations.find(a=>a.name===$('#search').value);if(a)focus(a);};
function updateLabels(){const occupied=[],level=scale/camera.zoom;for(const l of labels){if(!showLabels||l.a.priority>(level>650?1:level>230?2:3)){l.el.style.display='none';continue;}const p=l.p.clone().project(camera),x=(p.x*.5+.5)*innerWidth,y=(-p.y*.5+.5)*innerHeight;const w=l.a.name.length*13+24;let visible=p.z>-1&&p.z<1&&x>w/2&&x<innerWidth-w/2&&y>115&&y<innerHeight-76;const box=[x-w/2,y-28,x+w/2,y+6];if(visible&&occupied.some(b=>box[0]<b[2]+8&&box[2]>b[0]-8&&box[1]<b[3]+8&&box[3]>b[1]-8))visible=false;if(visible)occupied.push(box);l.el.style.display=visible?'block':'none';l.el.style.transform=`translate(${x}px,${y}px) translate(-50%,-100%)`;}}
function tick(){requestAnimationFrame(tick);controls.update();if(ready)updateLabels();renderer.render(scene,camera);}tick();
async function load(){try{await new Promise(r=>setTimeout(r,100));const str=$('#model').textContent.trim();const raw=atob(str),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);$('#model').remove();$('#load-status').textContent='正在布置校园…';await new Promise(r=>setTimeout(r,30));new GLTFLoader().parse(bytes.buffer,'',g=>{scene.add(g.scene);g.scene.traverse(o=>{if(o.isMesh&&o.material){o.castShadow=true;o.receiveShadow=true;const ms=Array.isArray(o.material)?o.material:[o.material];for(const m of ms){m.roughness=Math.max(m.roughness||0,.65);m.metalness=Math.min(m.metalness||0,.25);}}});ready=true;window.__campusReady=true;window.__campusAnnotations=annotations.length;$('#loading').remove();$('#count').textContent=`${annotations.length} 处名称标注`;},e=>fail(e));}catch(e){fail(e);}}
function fail(e){window.__campusError=String(e);$('#load-status').textContent='模型未能加载，请使用新版 Chrome 或 Edge 打开。';console.error(e);}
load();
