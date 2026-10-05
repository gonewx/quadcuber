"""压头两侧承载与后部避让的回归检查。

运行：python tools/lego/v3/test_dual_support.py。轴孔和表面来自 LDraw 几何。
"""
import unittest

import numpy as np

import model
import run_check  # noqa: F401
import check
import ldraw
import mechanical_audit as audit


class DualSupportTests(unittest.TestCase):
    def test_each_wheel_has_two_opposed_supports_and_a_flush_axle(self):
        """退回单侧薄梁、缩短轴或增加层外轴套，都应使本检查失败。"""
        parts = model.module(0, steps=False)
        for wheel in (p for p in parts if p.name == '42610.dat'):
            shafts = [p for p in parts if p.kind == 'axle' and np.linalg.norm(p.pos-wheel.pos)<1e-8]
            self.assertEqual(len(shafts), 1, '轮毂需要一根贯穿两侧的轴')
            shaft = shafts[0]
            thin = [p for p in parts if p.head and p.kind == 'solid' and
                    abs(np.ptp(ldraw.geometry(p.name)[0][:,:,1])-10)<1e-8]
            layers = check._pin_layers(shaft,thin)
            self.assertEqual(len(layers),2,'轮轴必须同时进入两根薄梁')
            spans = sorted((round(lo,6),round(hi,6)) for _,lo,hi in layers)
            self.assertEqual(spans,[(-20,-10),(10,20)])
            local = (audit.world(shaft).reshape(-1,3)-wheel.pos) @ wheel.rot
            self.assertLessEqual(float(abs(local[:,2]).max()),20,'轮轴不能伸入相邻层')

    def test_crank_shaft_clears_guide_frame_at_closure(self):
        """原闭合位置的曲柄轴实际伸入导向框；应保留正距离。"""
        import fcl
        parts = model.module(0,steps=False)
        shaft = next(p for p in parts if p.name=='32062.dat' and not p.head)
        guide = min((p for p in parts if p.name=='64179.dat' and np.allclose(p.pos[1:],[0,0])),
                    key=lambda p:np.linalg.norm(p.pos-shaft.pos))
        def obj(p):
            t=ldraw.geometry(p.name)[0]
            b=fcl.BVHModel();b.beginModel(len(t)*3,len(t))
            b.addSubModel(t.reshape(-1,3),np.arange(len(t)*3).reshape(-1,3));b.endModel()
            return fcl.CollisionObject(b,fcl.Transform(p.rot,p.pos))
        distance = fcl.distance(obj(shaft),obj(guide),fcl.DistanceRequest(),fcl.DistanceResult())
        self.assertGreaterEqual(distance*.4,2,'曲柄轴离导向框应有至少 2mm 名义余量')

    def test_crank_shaft_stays_outside_rotating_rod(self):
        """恢复靠推杆一侧的曲柄运动支路，会重新出现浅穿入。"""
        for stroke in np.linspace(0,model.OPEN_S,81):
            parts=model.module(float(stroke),steps=False)
            shaft=next(p for p in parts if p.name=='32062.dat' and not p.head)
            radii,_=audit.projected_minimum(audit.world(shaft))
            self.assertGreaterEqual((float(radii.min())-6)*.4,1)


if __name__ == '__main__':
    unittest.main()
