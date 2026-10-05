"""推杆缩短回归：限制悬伸，保留完整支承与插入深度，连接器不能撞导向框。"""
import unittest
import numpy as np
import fcl
import model
import run_check  # noqa: F401
import check
from mesh_clearance import obj,rod_socket_contact


class RodSupportTests(unittest.TestCase):
    def test_rod_length_and_front_overhang_are_reduced(self):
        for stroke in np.linspace(0,model.OPEN_S,25):
            parts=model.module(float(stroke),steps=False)
            rods=[p for p in parts if p.note in ('推杆短轴','推杆长轴')]
            extent=[p.pos[0]+end for p in rods for end in check.connector_bounds(p.name)]
            self.assertLessEqual((max(extent)-min(extent))*.4,104.+1e-8)
            joint=next(p for p in parts if p.note=='推杆铰接头')
            overhang=joint.pos[0]-model.MODULE_DX-max(model.ROD_BEARING_X)
            self.assertLessEqual(overhang*.4,48.)

    def test_shorter_rod_keeps_bearing_and_connector_engagement(self):
        for stroke in np.linspace(0,model.OPEN_S,25):
            parts=model.module(float(stroke),steps=False)
            long=next(p for p in parts if p.note=='推杆长轴')
            lo,hi=check.connector_bounds(long.name)
            for x in model.ROD_BEARING_X:
                center=x+model.MODULE_DX
                self.assertLessEqual(long.pos[0]+lo,center-10-10,
                                     '轴承后面保留至少4mm名义轴端余量')
                self.assertGreaterEqual(long.pos[0]+hi,center+10+10,
                                        '轴承前面保留至少4mm名义余量')
            sleeve=next(p for p in parts if p.note=='推杆连接器')
            short=next(p for p in parts if p.note=='推杆短轴')
            joint=next(p for p in parts if p.note=='推杆铰接头')
            for shaft,body in ((long,sleeve),(short,sleeve),(short,joint)):
                layers=check._pin_layers(shaft,[body])
                self.assertEqual(len(layers),1)
                self.assertGreaterEqual(layers[0][2]-layers[0][1],19.,
                                        '须完整覆盖约一孔深的实际孔段，不能靠少插来凑短轴')

    def test_connector_clears_the_front_bearing_over_the_whole_stroke(self):
        for stroke in np.linspace(0,model.OPEN_S,81):
            parts=model.module(float(stroke),steps=False)
            sleeve=next(p for p in parts if p.note=='推杆连接器')
            front=max(model.ROD_BEARING_X)+model.MODULE_DX
            guide=next(p for p in parts if p.name=='64179.dat' and not p.head
                       and np.allclose(p.pos[1:],0.) and abs(p.pos[0]+60-front)<1e-8)
            gap=fcl.distance(obj(sleeve),obj(guide),fcl.DistanceRequest(),fcl.DistanceResult())*.4
            self.assertGreaterEqual(gap,2.)

    def test_socket_contact_is_only_the_fixed_nominal_end_face(self):
        parts=model.module(0,steps=False)
        joint=next(p for p in parts if p.note=='推杆铰接头')
        sleeve=next(p for p in parts if p.note=='推杆连接器')
        self.assertTrue(rod_socket_contact(joint,sleeve))
        moved=sleeve.moved(np.eye(3));moved.pos[0]+=.01
        self.assertFalse(rod_socket_contact(joint,moved),
                         '0.004mm的真实过插也不能被端面舍入检查豁免')

    def test_small_transverse_force_does_not_hide_the_rod_bending_moment(self):
        from load_path_analysis import static_case
        result=static_case(.1*9.80665/2)['推杆前接头载荷']
        self.assertLess(abs(result['合力_xyz_N'][1]),1e-8)
        self.assertAlmostEqual(result['横向弯矩幅值_Nmm'],3.31445995403,places=8)


if __name__=='__main__':unittest.main()
