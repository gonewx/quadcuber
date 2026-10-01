"""生成真实 LEGO 3139b 轮胎套在半轴套后的名义形状；不代表经过实测的配合。"""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ldraw


def main():
    triangles = ldraw.geometry('3139b.dat')[0].copy()
    radius = np.hypot(triangles[:, :, 0], triangles[:, :, 1])
    # 半轴套外缘 R9；胎唇原 R8。径向截面积近似保持，轴向宽度不变。
    # 这只是可重复的碰撞包络近似，不能预测橡胶应力、滑移或保持力。
    deformed = np.where(radius < 9.0, 9.0, np.sqrt(radius * radius + 17.0))
    triangles[:, :, :2] *= (deformed / radius)[:, :, None]
    lines = ['0 LEGO 3139b 小轮胎套在半轴套上的名义变形示意',
             '0 Author: quadcuber; derived from LDraw 3139b by James Jessiman',
             '0 !LICENSE CC BY 4.0 https://creativecommons.org/licenses/by/4.0/',
             '0 // 修改：展开原网格，按名义径向伸张变形；未经实物验证。',
             '0 BFC CERTIFY CCW']
    lines += ['3 16 ' + ' '.join(f'{v:.5f}' for v in tri.ravel()) for tri in triangles]
    (Path(ldraw.CUSTOM) / 'grip_tyre.dat').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
