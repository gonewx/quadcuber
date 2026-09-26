import random
import unittest

from quadcuber.cube import invert, parse_moves, random_scramble
from quadcuber.machine import Machine, Turn
from quadcuber.planner import PlannerOptions, group_moves, plan
from quadcuber.simulate import verify_plan


class GroupTest(unittest.TestCase):
    def test_merge_same_axis(self):
        self.assertEqual(group_moves(parse_moves("R L' R")), [(("L", -1), ("R", 2))])

    def test_cancel_then_merge(self):
        self.assertEqual(group_moves(parse_moves("U R R' U")), [(("U", 2),)])


class PlannerTest(unittest.TestCase):
    def check_solves(self, moves, machine=None, **kw):
        machine = machine or Machine()
        p = plan(moves, machine, **kw)
        r = verify_plan(p, invert(moves), machine)
        self.assertTrue(r.solved, f"{moves}: {r.error}")
        return p

    def test_single_turn(self):
        p = self.check_solves(parse_moves("R"))
        self.assertEqual(p.steps, [(Turn("R", 1),)])

    def test_opposite_faces_in_parallel(self):
        p = self.check_solves(parse_moves("R L'"))
        self.assertEqual(len(p.steps), 1)
        self.assertAlmostEqual(p.total_time, Machine().timing.turn90)

    def test_u_needs_cube_rotation(self):
        p = self.check_solves(parse_moves("U"))
        self.assertEqual(p.stats()["cube_rotations"], 1)

    def test_random_sequences(self):
        rng = random.Random(11)
        for _ in range(8):
            self.check_solves(invert(random_scramble(20, rng)))

    def test_full_search_not_worse_than_window(self):
        rng = random.Random(5)
        moves = invert(random_scramble(10, rng))
        full = self.check_solves(moves, window=None)
        windowed = self.check_solves(moves, window=4, commit=2)
        self.assertLessEqual(full.total_time, windowed.total_time + 1e-9)

    def test_parallel_options_help(self):
        rng = random.Random(9)
        moves = invert(random_scramble(12, rng))
        fast = self.check_solves(moves)
        slow = self.check_solves(moves, options=PlannerOptions(False, False, False))
        self.assertLessEqual(fast.total_time, slow.total_time + 1e-9)

    def test_angle_limit(self):
        m = Machine(angle_limit=2)
        rng = random.Random(2)
        p = self.check_solves(invert(random_scramble(8, rng)), machine=m)
        for st in p.states:
            for g in st.grippers:
                self.assertLessEqual(abs(g.angle), 2)


if __name__ == "__main__":
    unittest.main()
