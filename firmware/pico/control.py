"""机械手旋转的位置控制 (与硬件无关)。

这个模块只做计算, 不访问引脚, 因此 MicroPython (Pico) 和 CPython (PC 上的单元测试) 都能运行。
为了兼容 MicroPython, 这里不用 dataclass、类型注解等语法。

所有角度都是**机械手角度** (度), 速度 度/秒, 加速度 度/秒²; 时间用微秒整数 (ticks_us)。

控制方式:
- 梯形速度曲线生成参考位置 p_ref / 速度 v_ref / 加速度 a_ref;
- 输出占空比 u = 速度前馈 + 加速度前馈 + Kp*位置误差 + Kd*速度误差 + Ki*积分 (+ 静摩擦补偿);
- 位置和速度都在目标附近的容差内并保持 settle 时间, 判定为到位;
- 输出饱和而几乎不动时判定为堵转, 误差过大判定为失控 (多半是马达或编码器接反), 都会立即停止。
"""

import math

# 状态
RUN = "run"
DONE = "done"
STALL = "stall"  # 堵转: 输出饱和但几乎不动
TIMEOUT = "timeout"  # 超时仍未到位
RUNAWAY = "runaway"  # 跟踪误差过大 (马达或编码器方向接反时会出现)

FAILED = (STALL, TIMEOUT, RUNAWAY)


def _sign(x):
    return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)


class Gains:
    """控制参数。默认值只是起点, 需要在实物上校准 (见 arm_test.py 的 speed / friction 命令)。"""

    def __init__(self, **kw):
        self.vmax = 600.0  # 曲线最高速度 (度/秒)
        self.amax = 6000.0  # 曲线加速度 (度/秒²)
        self.v_full = 1000.0  # 占空比 1.0 时的空载速度 (度/秒), 用于速度前馈
        self.tau = 0.05  # 马达机械时间常数 (秒), 用于加速度前馈
        self.kp = 0.03  # 占空比 / 度
        self.kd = 0.0008  # 占空比 / (度/秒)
        self.ki = 0.0  # 占空比 / (度·秒)
        self.kfs = 0.08  # 静摩擦补偿 (起转所需的占空比)
        self.umax = 1.0  # 占空比上限
        self.tol = 2.0  # 到位容差 (度)
        self.vtol = 60.0  # 到位时的速度容差 (度/秒)
        self.settle = 0.02  # 在容差内保持多久才算到位 (秒)
        self.timeout = 0.5  # 曲线结束后最多再等多久 (秒)
        self.stall_time = 0.15  # 输出饱和且不动持续多久判定为堵转 (秒)
        self.stall_vel = 20.0  # 低于这个速度算 "不动" (度/秒)
        self.max_err = 45.0  # 跟踪误差超过这个值判定为失控 (度)
        for k, v in kw.items():
            self.set(k, v)

    def names(self):
        return sorted(k for k in self.__dict__ if not k.startswith("_"))

    def set(self, name, value):
        if name not in self.__dict__:
            raise KeyError("未知参数: " + name)
        self.__dict__[name] = float(value)

    def as_dict(self):
        return {k: self.__dict__[k] for k in self.names()}


class Trapezoid:
    """从 p0 到 p1 的梯形速度曲线 (距离太短时退化为三角形)。"""

    def __init__(self, p0, p1, vmax, amax):
        self.p0 = p0
        self.p1 = p1
        d = p1 - p0
        self.s = 1.0 if d >= 0 else -1.0
        dist = abs(d)
        ta = vmax / amax
        if amax * ta * ta > dist:  # 到不了最高速度
            ta = math.sqrt(dist / amax)
            self.tc = 0.0
        else:
            self.tc = (dist - amax * ta * ta) / vmax
        self.ta = ta
        self.a = amax
        self.vp = amax * ta
        self.duration = 2 * ta + self.tc

    def at(self, t):
        """返回时刻 t (秒) 的 (位置, 速度, 加速度)。"""
        s, a, ta, tc, vp = self.s, self.a, self.ta, self.tc, self.vp
        if t <= 0:
            return self.p0, 0.0, 0.0
        if t >= self.duration:
            return self.p1, 0.0, 0.0
        if t < ta:
            return self.p0 + s * 0.5 * a * t * t, s * a * t, s * a
        da = 0.5 * a * ta * ta
        if t < ta + tc:
            return self.p0 + s * (da + vp * (t - ta)), s * vp, 0.0
        r = self.duration - t  # 距离结束还剩的时间
        return self.p1 - s * 0.5 * a * r * r, s * a * r, -s * a


class VelocityEstimator:
    """用最近若干个采样的位置差估计速度 (编码器分辨率有限, 相邻两次采样直接相减噪声太大)。"""

    def __init__(self, size=8):
        self.size = size
        self.ts = [0] * size
        self.ps = [0.0] * size
        self.n = 0
        self.i = 0

    def update(self, t_us, pos):
        size = self.size
        if self.n < size:
            self.n += 1
        j = (self.i - self.n + 1) % size  # 最旧的采样 (写入当前采样之前)
        self.ts[self.i] = t_us
        self.ps[self.i] = pos
        self.i = (self.i + 1) % size
        if self.n < 2:
            return 0.0
        dt = t_us - self.ts[j]
        if dt <= 0:
            return 0.0
        return (pos - self.ps[j]) * 1e6 / dt


class MoveController:
    """一次旋转: 反复调用 step(当前时间, 当前角度), 返回应输出的占空比。

    到位后继续调用 step 会保持在目标位置 (state 保持 DONE)。
    失败 (堵转 / 超时 / 失控) 后 step 始终返回 0, 调用方应立即停止马达。
    """

    def __init__(self, p0, p1, gains, t0_us):
        self.g = gains
        self.target = p1
        self.prof = Trapezoid(p0, p1, gains.vmax, gains.amax)
        self.t0 = t0_us
        self.vel = VelocityEstimator()
        self.state = RUN
        self.integ = 0.0
        self.t_reach = None  # 第一次进入位置容差的时刻 (秒, 相对开始)
        self.t_settle = None  # 最后一次进入 "位置+速度" 容差的时刻; 到位后即为到位耗时
        self.t_done = None  # 判定到位的时刻 (= t_settle + settle)
        self.overshoot = 0.0  # 越过目标的最大角度 (度)
        self.max_track_err = 0.0
        self.stall_since = None
        self.last_u = 0.0
        self.last_v = 0.0
        self.t_prev = 0.0

    def step(self, now_us, pos):
        g = self.g
        if self.state in FAILED:
            return 0.0
        t = (now_us - self.t0) / 1e6
        dt = t - self.t_prev
        self.t_prev = t
        p_ref, v_ref, a_ref = self.prof.at(t)
        v = self.vel.update(now_us, pos)
        self.last_v = v
        e = p_ref - pos
        err_final = self.target - pos

        ae = abs(e)
        if ae > self.max_track_err:
            self.max_track_err = ae
        over = -self.prof.s * err_final
        if over > self.overshoot:
            self.overshoot = over

        if ae > g.max_err:
            return self._fail(RUNAWAY)

        # 到位判定
        in_pos = abs(err_final) <= g.tol
        if in_pos and self.t_reach is None:
            self.t_reach = t
        if in_pos and abs(v) <= g.vtol:
            if self.t_settle is None:
                self.t_settle = t
            if self.state == RUN and t - self.t_settle >= g.settle and t >= self.prof.duration:
                self.state = DONE
                self.t_done = t
        else:
            if self.state == RUN:
                self.t_settle = None
        if self.state == RUN and t > self.prof.duration + g.timeout:
            return self._fail(TIMEOUT)

        # 控制律
        if g.ki:
            self.integ += e * dt  # 积分只用于消除小的静差
            lim = 0.3 / g.ki
            self.integ = max(-lim, min(lim, self.integ))
        u = v_ref / g.v_full + a_ref * g.tau / g.v_full + g.kp * e + g.kd * (v_ref - v) + g.ki * self.integ
        if abs(err_final) > g.tol * 0.5:  # 目标附近不加摩擦补偿, 否则会来回抖
            u += g.kfs * _sign(u)
        if u > g.umax:
            u = g.umax
        elif u < -g.umax:
            u = -g.umax

        # 堵转判定
        if abs(u) >= 0.95 * g.umax and abs(v) < g.stall_vel:
            if self.stall_since is None:
                self.stall_since = t
            elif t - self.stall_since >= g.stall_time:
                return self._fail(STALL)
        else:
            self.stall_since = None

        self.last_u = u
        return u

    def _fail(self, state):
        self.state = state
        self.last_u = 0.0
        return 0.0
