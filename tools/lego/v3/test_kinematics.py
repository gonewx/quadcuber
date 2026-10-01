"""平行夹块的运动学回归检查: python tools/lego/v3/test_kinematics.py。"""
import math
import unittest

import numpy as np

import model
import run_check  # noqa: F401: 加载连接件目录
import check
import four_arm
import ldraw


class ParallelJawTests(unittest.TestCase):
    def test_moving_links_and_pads_clear_all_module_parts(self):
        """夹块和输入连杆与全部零件互查，包含轴、销和轴套。"""
        for stroke in np.linspace(0, model.OPEN_S, 17):
            parts = model.module(float(stroke), steps=False)
            pads = [p for p in parts if p.head and p.color in (model.C_PAD, model.C_LINK)]
            self.assertEqual(len(pads), 6)
            boxes = {id(p): check._obb(p) for p in parts}
            for pad in pads:
                alo, ahi = boxes[id(pad)]
                for other in parts:
                    if other is pad:
                        continue
                    blo, bhi = boxes[id(other)]
                    if np.any(alo > bhi - 1) or np.any(blo > ahi - 1):
                        continue
                    hits = 0
                    for a, b in ((pad, other), (other, pad)):
                        sa, sb = check.Solid(a.name), check.Solid(b.name)
                        local = (sa.samples @ a.rot.T + a.pos - b.pos) @ b.rot
                        hits += int(sb.inside(local).sum())
                    self.assertLessEqual(hits, 3, (stroke, pad.name, other.name, other.pos.tolist(), hits))

    def test_four_bar_closes_and_keeps_pad_parallel(self):
        """从实件孔位验证闭环, 避免只验证绘图角度变量。"""
        for stroke in np.linspace(0, model.OPEN_S, 17):
            model.STEPS.clear()
            parts = model.module(float(stroke))
            for sign in (-1, 1):
                pick = lambda name: next(p for p in parts if p.name == name and p.head and p.pos[1] * sign > 0)
                main, follower, pad = map(pick, ("32524.dat", "11478.dat", "32056.dat"))
                a, c = (main.world([0, 0, z])[:2] for z in (-20, 60))
                b, d = (follower.world([0, 0, z])[:2] for z in (-40, 40))
                np.testing.assert_allclose(b - a, [model.PARALLEL_DX, sign * model.PARALLEL_DY], atol=1e-9)
                np.testing.assert_allclose(d - c, b - a, atol=1e-9)
                self.assertAlmostEqual(float(np.linalg.norm(c - a)), 80)
                self.assertAlmostEqual(float(np.linalg.norm(d - b)), 80)
                np.testing.assert_allclose(pad.world([40, 0, 0])[:2], c, atol=1e-9)
                np.testing.assert_allclose(pad.world([0, 0, 20])[:2], d, atol=1e-9)
                # 从动臂的十字孔固定轴, 两根轴的截面也必须随臂转动。
                for name, center in (("3737.dat", b), ("4519.dat", d)):
                    axle = next(p for p in parts if p.head and p.name == name and np.linalg.norm(p.pos[:2] - center) < 1e-8)
                    np.testing.assert_allclose(axle.rot[:, 1], follower.rot[:, 0], atol=1e-9)
                # L 梁接触边沿局部 X, 始终平行于世界 X。
                np.testing.assert_allclose(pad.rot[:, 0], [1, 0, 0], atol=1e-9)
                for anchor in (a, b):
                    supports = [p for p in parts if p.head and p.name in ("32523.dat", "32525.dat")
                                and abs(p.pos[0] - anchor[0]) < 1e-8]
                    aligned = []
                    for support in supports:
                        extent = 100 if support.name == "32525.dat" else 20
                        holes = [support.world([0, 0, z])[:2] for z in range(-extent, extent + 1, 20)]
                        if any(np.linalg.norm(h - anchor) < 1e-8 for h in holes):
                            aligned.append(support)
                    self.assertEqual(len(aligned), 2)

    def test_input_link_uses_round_holes_and_reduces_offset(self):
        for stroke in np.linspace(0, model.OPEN_S, 11):
            model.STEPS.clear()
            parts = model.module(float(stroke))
            for sign in (-1, 1):
                links = [p for p in parts if p.head and p.color == model.C_LINK and p.pos[2] * sign > 0]
                self.assertEqual(len(links), 1)
                link = links[0]
                self.assertEqual(link.name, "32526.dat")
                self.assertAlmostEqual(link.pos[2], 20 * sign)
                c = link.world([20, 0, 80])[:2]
                j = link.world([0, 0, 0])[:2]
                np.testing.assert_allclose(c, [model.CROSS_CLOSED_X - stroke + model.MODULE_DX, 0], atol=1e-9)
                main = next(p for p in parts if p.name == "32524.dat" and p.head and p.pos[1] * sign > 0)
                np.testing.assert_allclose(main.world([0, 0, -40])[:2], j, atol=1e-9)
                self.assertAlmostEqual(float(np.linalg.norm(j - c)), math.hypot(80, 20))

    def test_passive_joint_holes_are_round(self):
        # 主臂绕夹块固定轴转; 从动臂固定轴绕L 梁朝外一边的中间圆孔转。
        for name, centers in (("32524.dat", [[0, 0, z] for z in (-40, -20, 60)]),
                              ("32526.dat", [[0, 0, 0], [20, 0, 80]]),
                              ("32056.dat", [[0, 0, 20]])):
            solid = check.Solid(name)
            for ctr in centers:
                pts = np.array(ctr) + np.array([[3.5 * math.cos(a), 0, 3.5 * math.sin(a)]
                                                for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)])
                self.assertFalse(solid.inside(pts, deep=False).any(), (name, ctr))

    def test_nominal_contact_preload_is_only_in_pad(self):
        model.STEPS.clear()
        parts = model.module()
        pads = [p for p in parts if p.name == "jaw_pad.dat"]
        self.assertEqual(len(pads), 2)
        lo, hi = ldraw.bbox("jaw_pad.dat")
        self.assertAlmostEqual(hi[1] - lo[1], model.PAD_T)
        gap = (pads[0].pos[1] + lo[1]) - (pads[1].pos[1] - lo[1])
        gap_mm = gap * 0.4
        self.assertGreater(gap_mm, 55.5)
        self.assertLess(gap_mm, 56)
        rigid_gap = gap_mm + 2 * model.PAD_T * 0.4
        self.assertGreater(rigid_gap, 56, "塑料夹块不能穿进魔方")

    def test_servo_forward_and_inverse_match(self):
        h = model.CRANK_C[1] - model.BLOCK_Y
        maximum = math.sqrt((model.LINK2_L + model.CRANK_R) ** 2 - h*h) - math.sqrt((model.LINK2_L - model.CRANK_R) ** 2 - h*h)
        for stroke in np.linspace(0, maximum, 31):
            th, x0 = model.servo_theta_for(float(stroke))
            crank = model.CRANK_C + model.CRANK_R * np.array([math.cos(th), math.sin(th)])
            x = crank[0] + math.sqrt(model.LINK2_L**2 - (crank[1] - model.BLOCK_Y)**2)
            self.assertAlmostEqual(x0 - x, stroke, places=8)
        for stroke in (-1, maximum + 1):
            with self.assertRaises(ValueError):
                model.servo_theta_for(stroke)
        for stroke in (-1, 1000):
            with self.assertRaises(ValueError):
                model.jaw_beta(stroke)

    def test_rotating_head_clears_own_drive_and_servo_joints(self):
        # 后架曾碰齿轮轴, 张开时曲柄端轴套曾碰推杆; 仅查相邻机械手会漏掉这两处。
        for stroke in (0, model.OPEN_S):
            for angle in (30, 45, 90, 225):
                parts = model.module(stroke, angle, steps=False)
                for part in parts:
                    part.arm = "L"
                self.assertFalse(four_arm.cross_hits(parts), (stroke, angle))

    def test_cube_layer_is_one_third_of_full_side(self):
        self.assertAlmostEqual(four_arm.LAYER, 140 / 3)
        # 轴落在旧版漏扫的半层里, 也必须影响间隙结果。
        axle = model.Part("4519.dat", 0, [-30, 90, 0], model.ALONG_Z, 0)
        axle.arm = "F"
        r = four_arm.min_radius([axle], "F", -72, -70 + four_arm.LAYER + 2)
        self.assertLess(r, four_arm.CUBE_R)


if __name__ == "__main__":
    unittest.main()
