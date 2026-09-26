"""魔方的贴纸模型 (世界坐标系), 用于独立验证规划结果。

坐标系 (右手系): x 轴指向 R, y 轴指向 U, z 轴指向 F。
每个贴纸由所在小块的位置 pos (各分量取 -1/0/1) 和朝外的法向量 normal 表示。
"""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Tuple

Vec = Tuple[int, int, int]

FACES = "URFDLB"
FACE_NORMALS: Dict[str, Vec] = {
    "U": (0, 1, 0),
    "D": (0, -1, 0),
    "R": (1, 0, 0),
    "L": (-1, 0, 0),
    "F": (0, 0, 1),
    "B": (0, 0, -1),
}
NORMAL_FACE: Dict[Vec, str] = {v: k for k, v in FACE_NORMALS.items()}


def axis_sign(face: str) -> Tuple[int, int]:
    """面所在的坐标轴 (0=x, 1=y, 2=z) 和方向 (+1/-1)。"""
    n = FACE_NORMALS[face]
    for axis in range(3):
        if n[axis]:
            return axis, n[axis]
    raise ValueError(face)


def rot90(v: Vec, axis: int) -> Vec:
    """绕 +axis 轴旋转 +90 度 (右手定则)。"""
    x, y, z = v
    if axis == 0:
        return (x, -z, y)
    if axis == 1:
        return (z, y, -x)
    return (-y, x, z)


def rotate(v: Vec, axis: int, quarters: int) -> Vec:
    for _ in range(quarters % 4):
        v = rot90(v, axis)
    return v


def face_quarters(face: str, k: int) -> Tuple[int, int, int]:
    """把 "从面外侧看顺时针转 k 个 90 度" 换算成 (axis, sign, 绕 +axis 的四分之一圈数)。

    顺时针 (从外侧看) 等于绕外法向量转 -90 度。
    """
    axis, sign = axis_sign(face)
    return axis, sign, -sign * k


# ---------------------------------------------------------------------------
# 转动记号
# ---------------------------------------------------------------------------

Move = Tuple[str, int]  # (面, k), k 取 1 / 2 / -1


def parse_moves(text: str) -> List[Move]:
    """解析 "R U R' U2" 这样的标准记号。"""
    moves: List[Move] = []
    for token in text.replace(",", " ").split():
        face = token[0].upper()
        if face not in FACE_NORMALS:
            raise ValueError(f"无法识别的转动: {token}")
        rest = token[1:]
        if rest in ("", "1"):
            k = 1
        elif rest in ("2", "2'"):
            k = 2
        elif rest in ("'", "3", "-"):
            k = -1
        else:
            raise ValueError(f"无法识别的转动: {token}")
        moves.append((face, k))
    return moves


def format_moves(moves: Iterable[Move]) -> str:
    out = []
    for face, k in moves:
        k = normalize_k(k)
        out.append(face + {1: "", 2: "2", -1: "'"}[k])
    return " ".join(out)


def normalize_k(k: int) -> int:
    """四分之一圈数规范到 1 / 2 / -1 (0 表示不动)。"""
    k %= 4
    return {0: 0, 1: 1, 2: 2, 3: -1}[k]


def invert(moves: Iterable[Move]) -> List[Move]:
    return [(f, normalize_k(-k)) for f, k in reversed(list(moves))]


def random_scramble(length: int, rng: random.Random) -> List[Move]:
    """随机打乱, 相邻两步不转同一个面, 也不出现 "同轴三连" 这类冗余。"""
    moves: List[Move] = []
    while len(moves) < length:
        face = rng.choice(FACES)
        if moves and moves[-1][0] == face:
            continue
        if (
            len(moves) >= 2
            and axis_sign(moves[-1][0])[0] == axis_sign(face)[0]
            and axis_sign(moves[-2][0])[0] == axis_sign(face)[0]
        ):
            continue
        moves.append((face, rng.choice((1, 2, -1))))
    return moves


# ---------------------------------------------------------------------------
# 贴纸魔方
# ---------------------------------------------------------------------------


class Cube:
    """54 个贴纸的魔方, 所有操作都在世界坐标系中进行。"""

    def __init__(self) -> None:
        self.stickers: Dict[Tuple[Vec, Vec], str] = {}
        for face, n in FACE_NORMALS.items():
            axis = next(i for i in range(3) if n[i])
            others = [i for i in range(3) if i != axis]
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    pos = [0, 0, 0]
                    pos[axis] = n[axis]
                    pos[others[0]] = a
                    pos[others[1]] = b
                    self.stickers[(tuple(pos), n)] = face

    def copy(self) -> "Cube":
        c = Cube.__new__(Cube)
        c.stickers = dict(self.stickers)
        return c

    def turn_layer(self, axis: int, sign: int, quarters: int) -> None:
        """把 pos[axis] == sign 的那一层绕 +axis 转 quarters 个 90 度。"""
        new = {}
        for (pos, n), color in self.stickers.items():
            if pos[axis] == sign:
                pos, n = rotate(pos, axis, quarters), rotate(n, axis, quarters)
            new[(pos, n)] = color
        self.stickers = new

    def rotate_all(self, axis: int, quarters: int) -> None:
        """整个魔方绕 +axis 转 quarters 个 90 度。"""
        self.stickers = {
            (rotate(pos, axis, quarters), rotate(n, axis, quarters)): color
            for (pos, n), color in self.stickers.items()
        }

    def move(self, face: str, k: int) -> None:
        """转动世界坐标中朝向 face 的那一层 (从外侧看顺时针 k 个 90 度)。"""
        axis, sign, q = face_quarters(face, k)
        self.turn_layer(axis, sign, q)

    def apply(self, moves: Iterable[Move]) -> "Cube":
        for face, k in moves:
            self.move(face, k)
        return self

    def face_colors(self, face: str) -> List[str]:
        n = FACE_NORMALS[face]
        return [c for (pos, nn), c in self.stickers.items() if nn == n]

    def is_solved(self) -> bool:
        """每个面颜色一致即为还原 (不要求整体朝向与初始相同)。"""
        return all(len(set(self.face_colors(f))) == 1 for f in FACES)
