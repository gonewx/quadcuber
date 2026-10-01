"""防翻折回归：正常开度留隙，实体限位必须在两组运动解汇合前阻挡主臂。"""
import math
import unittest

import fcl
import numpy as np
import model
import run_check  # noqa: F401
import check
from mesh_clearance import obj


def distance(a,b):
    return fcl.distance(obj(a),obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4


class OpenStopTests(unittest.TestCase):
    def test_each_jaw_meets_a_two_sided_stop_before_the_toggle(self):
        parts=model.module(0,steps=False)
        stops=[p for p in parts if p.note=='开限位挡轴']
        self.assertEqual(len(stops),2,'上下夹指各需要独立实体开限位')
        tangent=math.atan2(model.JAW_Y,math.sqrt((model.JAW_A+model.LINK_L)**2-model.JAW_Y**2))
        for stop in stops:
            sy=np.sign(stop.pos[1])
            pivot=np.array([model.PIVOT_X+model.MODULE_DX,sy*model.JAW_Y,0.])
            beam=model.Part('32524.dat',4,pivot,model.I,0)
            def at(deg):
                beam.rot=model.rot_z(sy*math.radians(deg))@model.BEAM_X_HOLES_Z
                return distance(beam,stop)
            self.assertGreaterEqual(at(math.degrees(model.OPEN_BETA)),1.)
            self.assertLessEqual(at(35),1e-6,'35°时应已被挡住，不能继续去往约41.81°汇合点')
            lo,hi=25.,35.
            for _ in range(30):
                mid=(lo+hi)/2
                if at(mid)<=1e-7:hi=mid
                else:lo=mid
            self.assertLess(hi,math.degrees(tangent)-8,'限位必须留出角度裕量')
            layers=check._pin_layers(stop,[p for p in parts if p.note=='限位支架'])
            self.assertEqual(len(layers),4,'挡轴两端各穿入两片支架，不能只有一侧承载')
            self.assertEqual(sorted((round(lo),round(hi)) for _,lo,hi in layers),
                             [(-70,-60),(-60,-50),(50,60),(60,70)])

    def test_module_rejects_a_command_past_normal_opening(self):
        with self.assertRaises(ValueError):
            model.module(model.OPEN_S+.1,steps=False)

    def test_alternative_assembly_branch_exists_without_stops(self):
        dx=model.PIVOT_X-model.CROSS_CLOSED_X
        radius=math.hypot(dx,model.JAW_Y)
        alpha=math.atan2(model.JAW_Y,dx)
        delta=math.acos((radius**2+model.JAW_A**2-model.LINK_L**2)/(2*radius*model.JAW_A))
        angles=[alpha-delta,alpha+delta]
        for beta in angles:
            joint=np.array([model.PIVOT_X-model.JAW_A*math.cos(beta),model.JAW_Y-model.JAW_A*math.sin(beta)])
            self.assertAlmostEqual(np.linalg.norm(joint-[model.CROSS_CLOSED_X,0]),model.LINK_L)
        self.assertGreater(math.degrees(angles[1]),90)


if __name__=='__main__':
    unittest.main()
