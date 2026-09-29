// 说明书里可旋转的 3D 模型 (booklet.py 复制到 docs/lego/v3/viewer.js)。
// 读取同目录的 model.mpd (整机 + 全部零件几何, 按步骤分段), 用 three.js 的 LDrawLoader 解析。
// 页面里要有: #v3d (放画布的容器)、#v3d-step (步骤滑块)、#v3d-label (步骤名)、#v3d-status (加载提示)、
// window.V3D_STEPS = [步骤名, ...]。
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LDrawLoader } from 'three/addons/loaders/LDrawLoader.js';
import { LDrawConditionalLineMaterial } from 'three/addons/materials/LDrawConditionalLineMaterial.js';

const box = document.getElementById('v3d');
const slider = document.getElementById('v3d-step');
const label = document.getElementById('v3d-label');
const status = document.getElementById('v3d-status');
const names = window.V3D_STEPS || [];

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
box.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(getComputedStyle(box).getPropertyValue('--v3d-bg').trim() || '#f4f3ef');
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8a8a, 2.3));
const dl = new THREE.DirectionalLight(0xffffff, 1.5);
dl.position.set(-1, 2, 1.5);
scene.add(dl);
const camera = new THREE.PerspectiveCamera(35, 1, 1, 20000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

function resize() {
  const w = box.clientWidth, h = box.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(box);
resize();

let group = null;
let fitted = false;

function showStep(n) {
  if (!group) return;
  for (const c of group.children) {
    const st = (c.userData.buildingStep ?? 0) + 1;  // 第 1 步的零件 buildingStep 为 0
    c.visible = st <= n;
    c.traverse(o => {
      if (!o.material || !o.userData.baseMaterial) return;
      o.material = st === n && n < names.length ? o.userData.hiMaterial : o.userData.baseMaterial;
    });
  }
  label.textContent = n >= names.length ? `全部 ${names.length} 步` : `第 ${n} 步 · ${names[n - 1]}`;
}

function fit() {
  const b = new THREE.Box3();
  for (const c of group.children) if (c.visible) b.expandByObject(c);
  const ctr = b.getCenter(new THREE.Vector3());
  const r = b.getSize(new THREE.Vector3()).length() / 2 || 100;
  const dir = new THREE.Vector3(0.55, 0.5, 0.67).normalize();
  camera.position.copy(ctr).addScaledVector(dir, r / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * 0.9);
  camera.near = r / 50; camera.far = r * 50; camera.updateProjectionMatrix();
  controls.target.copy(ctr);
  controls.update();
}

const loader = new LDrawLoader();
loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
loader.smoothNormals = true;
fetch('model.mpd').then(r => {
  if (!r.ok) throw new Error(r.status);
  return r.text();
}).then(text => new Promise((res, rej) => loader.parse(text, res, rej))).then(g => {
  group = g;
  group.rotation.x = Math.PI;  // LDraw -Y 向上
  scene.add(group);
  // 当前步骤的新零件用高亮材质 (提亮), 方便看出这一步加了什么
  group.traverse(o => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const hi = mats.map(m => { const k = m.clone(); k.emissive = new THREE.Color(0x3a2a00); return k; });
    o.userData.baseMaterial = o.material;
    o.userData.hiMaterial = Array.isArray(o.material) ? hi : hi[0];
  });
  slider.max = String(names.length);
  slider.value = String(names.length);
  slider.disabled = false;
  showStep(names.length);
  fit();
  status.hidden = true;
}).catch(e => {
  status.textContent = '3D 模型加载失败 (' + e.message + '), 下面的步骤图不受影响。';
});

slider.addEventListener('input', () => showStep(Number(slider.value)));
document.getElementById('v3d-fit').addEventListener('click', () => group && fit());

(function loop() {
  requestAnimationFrame(loop);
  controls.update();
  renderer.render(scene, camera);
})();
window.v3dReady = () => group !== null;
