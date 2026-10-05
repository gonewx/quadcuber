"""将官方轮胎网格映射到用户指定 14×6mm 外包络，保留轮毂安装内槽。"""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ldraw


def main():
    triangles = ldraw.geometry('50945.dat')[0].copy()
    radius = np.hypot(triangles[:, :, 0], triangles[:, :, 1])
    target = np.where(radius <= 14, radius, 14 + (radius - 14) * 3.5 / (radius.max() - 14))
    triangles[:, :, :2] *= (target / radius)[:, :, None]
    triangles[:, :, 2] *= 7.5 / np.abs(triangles[:, :, 2]).max()
    lines = ['0 LEGO 50945 轮胎，用户指定名义尺寸 14x6mm',
             '0 Author: quadcuber; derived from LDraw 50945/50951 by Michael Heidemann',
             '0 !LICENSE CC BY 4.0 https://creativecommons.org/licenses/by/4.0/',
             '0 // 修改：保留径向内槽，调整外包络至14x6mm；不代表实测变形。',
             '0 BFC CERTIFY CCW']
    lines += ['3 16 ' + ' '.join(f'{v:.5f}' for v in tri.ravel()) for tri in triangles]
    (Path(ldraw.CUSTOM) / '50945_nominal.dat').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
