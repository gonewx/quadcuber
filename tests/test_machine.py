import unittest

from quadcuber.machine import (
    Close,
    CubeRotate,
    InvalidStep,
    Machine,
    Open,
    Rotate,
    Turn,
    initial_state,
    rotate_orientation,
)


class MachineRulesTest(unittest.TestCase):
    def setUp(self):
        self.m = Machine(profile="generic")
        self.s0 = initial_state()

    def assertInvalid(self, state, step):
        with self.assertRaises(InvalidStep):
            self.m.check(state, step)

    def test_all_ring_faces_turnable_at_start(self):
        for p in "RLFB":
            self.m.check(self.s0, (Turn(p, 1),))

    def test_horizontal_bar_blocks_perpendicular_turn(self):
        s = self.m.apply(self.s0, (Turn("R", 1),))  # R 的夹条变成水平
        self.assertInvalid(s, (Turn("F", 1),))
        self.m.check(s, (Turn("L", 1),))  # 相对的面不受影响
        s = self.m.apply(s, (Open("R"),))
        self.m.check(s, (Turn("F", 1),))  # 松开 R 后可以拧 F

    def test_half_turn_keeps_bar_vertical(self):
        s = self.m.apply(self.s0, (Turn("R", 2),))
        self.m.check(s, (Turn("F", 1),))

    def test_support_required(self):
        self.assertInvalid(self.s0, (Open("R"), Open("F")))
        self.m.check(self.s0, (Open("R"), Open("L")))

    def test_turn_needs_anchor(self):
        s = self.m.apply(self.s0, (Open("F"), Open("B")))
        self.assertInvalid(s, (Turn("R", 1),))

    def test_no_adjacent_horizontal(self):
        m = Machine(no_adjacent_horizontal=True)
        s = m.apply(self.s0, (Turn("R", 1),))  # R 水平夹紧
        s = m.apply(s, (Open("R"),))
        # generic 旧抽象规则允许松开的 R 水平时拧 F; v3 结构下 F 的夹指会撞上 R 的夹指
        self.m.check(s, (Turn("F", 1),))
        with self.assertRaises(InvalidStep):
            m.check(s, (Turn("F", 1),))
        m.check(s, (Rotate("R", 1),))  # 先把 R 转回竖直
        s2 = m.apply(self.s0, (Open("F"), Open("B")))
        with self.assertRaises(InvalidStep):
            m.check(s2, (Rotate("F", 1), Rotate("R", 1)))  # R 夹紧不能空转, 换成相邻的同时空转
        s3 = m.apply(self.s0, (Open("R"), Open("L")))
        with self.assertRaises(InvalidStep):
            m.check(s3, (Rotate("R", 1), Turn("F", 1)))  # 相邻两个同一步转动

    def test_double_turn_only_opposite(self):
        self.m.check(self.s0, (Turn("R", 1), Turn("L", -1)))
        self.assertInvalid(self.s0, (Turn("R", 1), Turn("F", 1)))

    def test_cube_rotation_needs_other_pair_open(self):
        self.assertInvalid(self.s0, (CubeRotate(0, 1),))
        s = self.m.apply(self.s0, (Open("F"), Open("B")))
        s2 = self.m.apply(s, (CubeRotate(0, 1), Rotate("F", 1)))
        # 绕 x 轴 +90 度: 原来在上面的 U 面转到前面
        self.assertEqual(s2.world_of("U"), "F")

    def test_rotate_only_when_open(self):
        self.assertInvalid(self.s0, (Rotate("R", 1),))

    def test_cannot_mix_turn_and_grip(self):
        s = self.m.apply(self.s0, (Open("R"),))
        self.assertInvalid(s, (Turn("F", 1), Close("R")))

    def test_angle_limit(self):
        m = Machine(angle_limit=1)
        s = m.apply(initial_state(), (Turn("R", 1),))
        with self.assertRaises(InvalidStep):
            m.check(s, (Turn("R", 1),))
        m.check(s, (Turn("R", -1),))

    def test_orientation_rotation_is_permutation(self):
        o = rotate_orientation("URFDLB", 2, 1)
        self.assertEqual(sorted(o), sorted("URFDLB"))
        self.assertEqual(rotate_orientation(o, 2, -1), "URFDLB")

    def test_actions_are_not_confused(self):
        # NamedTuple 会让 Turn("F", 1) == Rotate("F", 1), 曾导致规划器缓存出错
        self.assertNotEqual(Turn("F", 1), Rotate("F", 1))
        self.assertNotEqual(Open("F"), Close("F"))


if __name__ == "__main__":
    unittest.main()
