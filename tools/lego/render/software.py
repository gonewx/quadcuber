"""从真实 LDraw 三角网格生成正交装配图，不依赖浏览器或本地 HTTP 服务。

用法：python software.py jobs.json。使用按深度排序的三角面绘制；不作为碰撞检查器。
"""
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ldraw


def palette():
    out = {}
    for line in ldraw.fetch_rel('colors/ldcfgalt.ldr').decode().splitlines():
        fields = line.split()
        if fields[:2] == ['0', '!COLOUR'] and 'CODE' in fields and 'VALUE' in fields:
            color = fields[fields.index('VALUE') + 1].lstrip('#')
            out[int(fields[fields.index('CODE') + 1])] = [int(color[n:n+2], 16) for n in (0, 2, 4)]
    return out


COLORS = palette()


def render(job):
    opts = job.get('opts', {})
    yaw, pitch = np.radians([opts.get('yaw', 35), opts.get('pitch', 30)])
    direction = np.array([math.sin(yaw)*math.cos(pitch), math.sin(pitch), math.cos(yaw)*math.cos(pitch)])
    right = np.array([math.cos(yaw), 0, -math.sin(yaw)])
    up = np.cross(direction, right)
    camera = np.diag([1, -1, -1]) @ np.stack([right, up, direction], axis=1)
    triangles, colors, fitting = [], [], []
    step = 0
    for line in Path(job['model']).read_text().splitlines():
        f = line.split()
        if f[:2] == ['0', 'STEP']:
            step += 1
        if len(f) < 15 or f[0] != '1' or step > opts.get('maxStep', 1e9):
            continue
        color = int(f[1]); numbers = np.array(list(map(float, f[2:14])))
        xyz, rot = numbers[:3], numbers[3:].reshape(3, 3)
        mesh, ids, _ = ldraw.geometry(' '.join(f[14:]))
        world = (mesh @ rot.T + xyz) @ camera
        ids = np.where(ids == 16, color, ids)
        rgb = np.array([COLORS.get(int(i), [150, 150, 150]) for i in ids], float)
        normal = np.cross(world[:, 1] - world[:, 0], world[:, 2] - world[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-12)
        light = np.array([-.35, .6, .72]); light /= np.linalg.norm(light)
        shade = .58 + .42 * np.abs(normal @ light)
        rgb *= shade[:, None]
        if step < opts.get('highlight', -1) and opts.get('fadeOld'):
            rgb = rgb * .55 + 255 * .45
        triangles.append(world)
        colors.append(np.clip(rgb, 0, 255).astype(np.uint8))
        if step >= opts.get('fitFrom', 0) and step <= opts.get('fitStep', 1e9):
            fitting.append(world[:, :, :2].reshape(-1, 2))
    faces = np.concatenate(triangles); rgb = np.concatenate(colors)
    fit = np.concatenate(fitting or [faces[:, :, :2].reshape(-1, 2)])
    low, high = fit.min(axis=0), fit.max(axis=0)
    w, h = opts.get('w', 900), opts.get('h', 700)
    scale = min(w / max(high[0]-low[0], 1), h / max(high[1]-low[1], 1)) * (1 - 2*opts.get('margin', .05))
    xy = (faces[:, :, :2] - (low + high)/2) * [scale, -scale] + [w/2, h/2]
    # 超采样改善小孔与斜边。轮廓保持来自零件几何，无推测补形。
    image = Image.new('RGB', (w*2, h*2), 'white'); draw = ImageDraw.Draw(image)
    for i in np.argsort(faces[:, :, 2].mean(axis=1), kind='stable'):
        p = xy[i]
        if p[:, 0].max() < 0 or p[:, 0].min() > w or p[:, 1].max() < 0 or p[:, 1].min() > h:
            continue
        draw.polygon([tuple(v) for v in p*2], fill=tuple(rgb[i]))
    image.resize((w, h), Image.Resampling.LANCZOS).save(job['out'])


if __name__ == '__main__':
    jobs = json.loads(Path(sys.argv[1]).read_text())
    for n, job in enumerate(jobs, 1):
        render(job)
        print(f'{n}/{len(jobs)} {Path(job["out"]).name}', flush=True)
