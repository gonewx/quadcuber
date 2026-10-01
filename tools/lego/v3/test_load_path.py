"""承重回归：公共接头须有前端横向支承，并与直推杆保留运动自由度。"""
import math
import unittest
import numpy as np
import model
import run_check  # noqa: F401
import check
import fcl
from mesh_clearance import obj


class LoadPathTests(unittest.TestCase):
    def test_crosshead_has_two_guides_and_an_articulated_drive(self):
        roots_at_closed=None
        for stroke in np.linspace(0,model.OPEN_S,9):
            parts=model.module(float(stroke),steps=False)
            couplers=[p for p in parts if p.note=='Watt横梁']
            guides=[p for p in parts if p.note=='Watt连杆']
            drives=[p for p in parts if p.note=='推杆铰接薄梁']
            self.assertEqual(len(couplers),2,'公共接头两侧需要承重导向，不能只依赖悬伸推杆')
            self.assertEqual(len(guides),4)
            self.assertEqual(len(drives),2)
            roots=[p for p in parts if p.note=='Watt根轴']
            root_positions=sorted(tuple(p.pos) for p in roots)
            if roots_at_closed is None:roots_at_closed=root_positions
            self.assertTrue(np.allclose(root_positions,roots_at_closed),'导向根部必须固定到侧架')
            center=next(p for p in parts if p.note=='Watt公共轴').pos
            drive=next(p for p in parts if p.note=='推杆铰接头').pos
            self.assertAlmostEqual(drive[1],0.)
            self.assertAlmostEqual(np.linalg.norm(center-drive),60.,places=7)
            for link in drives:
                points=[link.world([0,0,z]) for z in (-30.,30.)]
                self.assertLess(min(np.linalg.norm(q[:2]-center[:2]) for q in points),1e-8)
                self.assertLess(min(np.linalg.norm(q[:2]-drive[:2]) for q in points),1e-8)
            for coupler in couplers:
                self.assertLess(np.linalg.norm(coupler.pos[:2]-center[:2]),1e-8)
                side_guides=[g for g in guides if g.pos[2]*coupler.pos[2]>0]
                for z in (-40.,40.):
                    joint=coupler.world([0,0,z])
                    self.assertLess(min(np.linalg.norm(g.world([0,0,end])[:2]-joint[:2])
                                        for g in side_guides for end in (-40.,40.)),1e-8)
                for guide in side_guides:
                    self.assertLess(min(np.linalg.norm(guide.world([0,0,end])[:2]-root.pos[:2])
                                        for end in (-40.,40.) for root in roots),1e-8)
            if stroke==model.OPEN_S:
                self.assertGreater(abs(center[1]),1e-4,'检查必须覆盖近似直线导向的实际偏移')

    def test_holding_the_drive_removes_the_crosshead_vertical_mode(self):
        for stroke in np.linspace(0,model.OPEN_S,9):
            parts=model.module(float(stroke),steps=False)
            coupling=next(p for p in parts if p.note=='Watt横梁' and p.pos[2]>0)
            roots=sorted((p.pos[:2] for p in parts if p.note=='Watt根轴' and p.pos[2]>0),key=lambda p:p[0])
            C=coupling.pos[:2]
            ends=[coupling.world([0,0,z])[:2] for z in (-40.,40.)]
            rows=[]
            for end,root in zip(ends,roots):
                direction=(end-root)/np.linalg.norm(end-root)
                arm=end-C
                rows.append([*direction,direction@np.array([-arm[1],arm[0]])/40.])
            D=next(p for p in parts if p.note=='推杆铰接头').pos[:2]
            rows.append([*((C-D)/np.linalg.norm(C-D)),0.])
            self.assertGreater(np.linalg.svd(rows,compute_uv=False).min(),.2,
                               '固定推杆后，公共接头不能仍有竖向刚体自由度')

    def test_normal_opening_and_jaw_link_closure(self):
        for stroke in np.linspace(0,model.OPEN_S,9):
            parts=model.module(float(stroke),steps=False)
            for sy in (-1,1):
                jaw=next(p for p in parts if p.name=='32524.dat' and p.color==model.C_JAW and p.pos[1]*sy>0)
                angle=abs(math.atan2(jaw.rot[1,2],jaw.rot[0,2]))
                self.assertLessEqual(angle,model.OPEN_BETA+1e-9)
                link=next(p for p in parts if p.note=='输入薄连杆' and p.pos[1]*sy>0)
                joint=jaw.world([0,0,-40])
                self.assertLess(min(np.linalg.norm(link.world([0,0,z])[:2]-joint[:2]) for z in (-40.,40.)),1e-8)

    def test_input_axle_stop_captures_the_link_and_clears_the_guides(self):
        for stroke in np.linspace(0,model.OPEN_S,9):
            parts=model.module(float(stroke),steps=False)
            guides=[p for p in parts if p.note=='Watt连杆']
            for axle in (p for p in parts if p.note=='输入关节轴'):
                self.assertEqual(axle.name,'24316.dat')
                sy=1 if axle.pos[1]>0 else -1
                link=next(p for p in parts if p.note=='输入薄连杆' and p.pos[1]*sy>0)
                self.assertAlmostEqual(axle.world([28.,0,0])[2],link.pos[2]+5*sy)
                for guide in guides:
                    gap=fcl.distance(obj(axle),obj(guide),fcl.DistanceRequest(),fcl.DistanceResult())*.4
                    self.assertGreaterEqual(gap,1.,'止挡轴不能侵占摆杆的运动空间')

    def test_side_frame_has_fixed_corners_and_a_keyed_rear_connection(self):
        parts=model.module(0,steps=False)
        corners=[p for p in parts if p.note=='前角梁']
        self.assertEqual(len(corners),4,'每侧上下角都需两点固定，不能组成可剪切的四连杆')
        connectors=[p for p in parts if p.kind in ('pin','axle')]
        for corner in corners:
            root=next(p for p in parts if p.name=='32525.dat' and p.head and p.pos[2]*corner.pos[2]>0)
            rail=next(p for p in parts if p.note=='侧架长梁' and p.pos[2]*corner.pos[2]>0 and p.pos[1]*corner.pos[1]>0)
            for other in (root,rail):
                joints=[p for p in connectors if len(check._pin_layers(p,[corner,other]))==2]
                self.assertGreaterEqual(len({tuple(np.round(p.pos[:2],5)) for p in joints}),2)
        rear=[p for p in parts if p.note=='转盘后横梁']
        self.assertEqual(len(rear),2)
        for beam in rear:
            pins=[p for p in parts if p.note=='转盘轴销' and p.pos[2]*beam.pos[2]>0]
            self.assertEqual(len(pins),2)
            for pin in pins:
                self.assertEqual(pin.name,'3749.dat')
                short=next(p for p in parts if p.note=='后短连接梁' and p.pos[2]*pin.pos[2]>0 and p.pos[1]*pin.pos[1]>0)
                layers=check._pin_layers(pin,[beam,short])
                self.assertEqual(len(layers),2)
                self.assertTrue(all(hi<=1e-8 and hi-lo>9.9 for _,lo,hi in layers),
                                '两片固定角的十字孔必须共用轴销的轴段')

    def test_side_frame_clears_the_motor_retainer_through_a_whole_turn(self):
        from load_path_analysis import side_frame_gear_clearance
        self.assertGreaterEqual(side_frame_gear_clearance()['连续整圈下界_mm'],1.)

    def test_load_report_balances_axial_eccentricity(self):
        from load_path_analysis import static_case
        for stroke in (0., model.OPEN_S/2, model.OPEN_S):
            for preload in (0., 1.):
                result=static_case(.1*9.80665/2,preload,stroke)
                spatial=result['公共接头组合体空间平衡']
                self.assertLess(spatial['力平衡残差_N'],1e-9)
                self.assertLess(spatial['力矩平衡残差_Nmm'],1e-8)
                if stroke==0 and preload==0:
                    moment=spatial['输入杆偏心力矩_Nmm']
                    self.assertAlmostEqual(moment[0],12.4808814357,places=7)
                    self.assertAlmostEqual(moment[1],-3.31445997,places=6)
                    guides=spatial['各侧前后摆杆轴力_N']
                    self.assertGreater(abs(guides['正Z'][0]),abs(guides['负Z'][0])*3)
                    self.assertNotIn('每侧各导向杆轴力_N',result)

    def test_round_pins_do_not_enter_cross_holes(self):
        self.assertEqual(run_check.pins_in_axle_holes(model.module(0,steps=False)),[])

    def test_base_rear_feet_are_connected(self):
        parts=model.build(with_cube=False)
        feet=[p for p in parts if p.note=='后端落地梁']
        self.assertEqual(len(feet),4,'固定结构后移后，每个后端应有落地支承')
        for foot in feet:
            connectors=[p for p in parts if p.note=='后端落地梁销' and check._pin_layers(p,[foot])]
            self.assertGreaterEqual(len(connectors),2)
            for pin in connectors:
                self.assertGreaterEqual(len(check._pin_layers(pin,[p for p in parts if p.kind=='solid'])),2)


if __name__=='__main__':unittest.main()
