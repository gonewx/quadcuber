"""回归：活动轴及推杆轴套不能占用开合所需的名义2mm余量。"""
import unittest

import fcl
import numpy as np

import model
import run_check  # noqa: F401
import check
import mechanical_audit
from mesh_clearance import obj


class MotionClearanceTests(unittest.TestCase):
    def test_guide_axles_clear_drive_and_its_retaining_bushes(self):
        """恢复向内伸出的旧活动轴，会在全开时只剩约0.265mm。"""
        for stroke in np.linspace(0,model.OPEN_S,81):
            parts=model.module(float(stroke),steps=False)
            shafts=[p for p in parts if p.note=='Watt活动轴']
            drive=[p for p in parts if p.note in ('推杆铰接薄梁','推杆铰轴半套')]
            for shaft in shafts:
                for p in drive:
                    gap=fcl.distance(obj(shaft),obj(p),fcl.DistanceRequest(),fcl.DistanceResult())*.4
                    self.assertGreaterEqual(gap,2.-1e-7,(stroke,shaft.pos,p.note,gap))

    def test_guide_axles_have_cross_hole_retention_and_full_bearing_depth(self):
        """去掉内轴套后，圆孔横梁不能代替十字孔固定；轴必须完整穿过两片薄梁。"""
        for stroke in (0.,model.OPEN_S):
            parts=model.module(stroke,steps=False)
            couplers=[p for p in parts if p.note=='Watt横梁']
            guides=[p for p in parts if p.note=='Watt连杆']
            bushes=[p for p in parts if p.note=='活动轴半套']
            for shaft in (p for p in parts if p.note=='Watt活动轴'):
                fixed=check._pin_layers(shaft,couplers)
                moving=check._pin_layers(shaft,guides)
                keeper=check._pin_layers(shaft,bushes)
                self.assertEqual(len(fixed),1)
                self.assertEqual(len(moving),1)
                self.assertEqual(len(keeper),1)
                for _,lo,hi in fixed+moving+keeper:self.assertAlmostEqual(hi-lo,10.)
                for p,_,_ in fixed+keeper:
                    alignment=abs(float(shaft.rot[:,1]@p.rot[:,0]))
                    self.assertLess(min(alignment,abs(1.-alignment)),1e-9,
                                    '十字轴与横梁端孔、外半轴套须保持相同的十字相位')
                # 横梁端孔在半径3.5LDU处应有十字孔角部实体，摆杆圆孔则全空。
                for layers,want in ((fixed,4),(moving,0)):
                    p,lo,hi=layers[0]
                    center=shaft.pos+(lo+hi)/2*shaft.rot[:,0]
                    probes=[p.rot.T@(center+3.5*(np.cos(a)*shaft.rot[:,1]+np.sin(a)*shaft.rot[:,2])-p.pos)
                            for a in np.radians(np.arange(0,360,45))]
                    self.assertEqual(int(check.Solid(p.name).inside(np.array(probes),deep=False).sum()),want)
                # 摆杆的两个轴向端面分别贴横梁与外半轴套，不留可脱离的装配空隙。
                segments=sorted((lo,hi) for _,lo,hi in fixed+moving+keeper)
                self.assertAlmostEqual(segments[0][1],segments[1][0])
                self.assertAlmostEqual(segments[1][1],segments[2][0])

    def test_guide_drive_clearance_has_a_continuous_bound(self):
        result=mechanical_audit.guide_drive_clearance()
        self.assertGreaterEqual(result['活动轴对驱动薄梁轴向下界_mm'],2.)
        self.assertGreaterEqual(result['活动轴对驱动半轴套径向下界_mm'],1.9999)
        self.assertGreaterEqual(result['连续开合间隙下界_mm'],1.9999)

    def test_rear_rotating_bush_envelope_clears_servo_link(self):
        """连杆多余孔朝推杆时，后部旋转轴套包络仅剩约0.878mm。"""
        result=mechanical_audit.rotating_bush_checks()
        self.assertGreaterEqual(result['最差']['连续回转间隙下界_mm'],2.)


if __name__=='__main__':unittest.main()
