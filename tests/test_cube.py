import random
import unittest

from quadcuber.cube import Cube, format_moves, invert, parse_moves, random_scramble


class CubeTest(unittest.TestCase):
    def test_four_quarter_turns_is_identity(self):
        for face in "URFDLB":
            c = Cube()
            for _ in range(4):
                c.move(face, 1)
            self.assertEqual(c.stickers, Cube().stickers, face)

    def test_sexy_move_order_6(self):
        c = Cube()
        for _ in range(6):
            c.apply(parse_moves("R U R' U'"))
        self.assertEqual(c.stickers, Cube().stickers)
        c = Cube().apply(parse_moves("R U R' U'"))
        self.assertFalse(c.is_solved())

    def test_scramble_then_inverse(self):
        rng = random.Random(3)
        for _ in range(20):
            s = random_scramble(25, rng)
            c = Cube().apply(s).apply(invert(s))
            self.assertEqual(c.stickers, Cube().stickers)

    def test_u_clockwise_moves_front_to_left(self):
        # U 顺时针 (从上往下看): 前面最上一行转到左面
        c = Cube().apply(parse_moves("U"))
        self.assertEqual(c.stickers[((-1, 1, 0), (-1, 0, 0))], "F")

    def test_whole_rotation_keeps_solved(self):
        for axis in range(3):
            c = Cube()
            c.rotate_all(axis, 1)
            self.assertTrue(c.is_solved())

    def test_parse_format_roundtrip(self):
        text = "R U2 F' L D B2"
        self.assertEqual(format_moves(parse_moves(text)), text)
        with self.assertRaises(ValueError):
            parse_moves("X")


if __name__ == "__main__":
    unittest.main()
