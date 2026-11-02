"""PyBullet Laikago 用の開ループ歩容（静的テスト可能）。

公式例 (bullet3 laikago.py) に合わせる:
- 初期姿勢クォータニオン: [0, 0.5, 0.5, 0]  ※単位だと縦向きに見える
- jointDirections / jointOffsets で目標角を変換
"""

from __future__ import annotations

import math
from typing import Sequence

# 公式 laikago.py と同じ
JOINT_DIRECTIONS: tuple[float, ...] = (-1, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1)
JOINT_OFFSETS: tuple[float, ...] = (
    0.0,
    -0.7,
    0.7,
    0.0,
    -0.7,
    0.7,
    0.0,
    -0.7,
    0.7,
    0.0,
    -0.7,
    0.7,
)

# 公式スポーン（単位クォータニオンではない）
SPAWN_POS: tuple[float, float, float] = (0.0, 0.0, 0.5)
SPAWN_ORN: tuple[float, float, float, float] = (0.0, 0.5, 0.5, 0.0)

# 対角トロット位相（FR+RL / FL+RR）: 脚インデックス 0..3
LEG_PHASE: tuple[float, ...] = (0.0, math.pi, math.pi, 0.0)


def apply_joint_map(
    motion: Sequence[float],
    *,
    directions: Sequence[float] = JOINT_DIRECTIONS,
    offsets: Sequence[float] = JOINT_OFFSETS,
) -> list[float]:
    """モーション空間の12角 → 実関節角。"""
    if len(motion) != 12:
        raise ValueError("motion は12要素である必要があります")
    return [float(directions[i]) * float(motion[i]) + float(offsets[i]) for i in range(12)]


def standing_targets() -> list[float]:
    """立位（モーション0 = 公式 offset のみ）。"""
    return apply_joint_map([0.0] * 12)


def trot_motion(step: int, *, dt: float = 1.0 / 240.0, freq: float = 1.5, amp: float = 0.25) -> list[float]:
    """12関節のモーション角（offset適用前）。"""
    if step < 0:
        raise ValueError("step は 0 以上である必要があります")
    if dt <= 0 or freq <= 0:
        raise ValueError("dt / freq は正である必要があります")
    w = 2.0 * math.pi * freq * step * dt
    motion = [0.0] * 12
    for leg in range(4):
        s = math.sin(w + LEG_PHASE[leg])
        base = leg * 3
        motion[base + 0] = 0.05 * s  # hip
        motion[base + 1] = amp * s  # thigh
        motion[base + 2] = -amp * max(0.0, s)  # calf 持ち上げ
    return motion


def trot_targets(step: int, *, dt: float = 1.0 / 240.0, freq: float = 1.5, amp: float = 0.25) -> list[float]:
    return apply_joint_map(trot_motion(step, dt=dt, freq=freq, amp=amp))


def frames_budget(duration_s: float, fps: int, sim_hz: int = 240) -> tuple[int, int, int]:
    """(steps, every, max_frames)。"""
    if duration_s <= 0 or fps <= 0 or sim_hz <= 0:
        raise ValueError("duration_s / fps / sim_hz は正である必要があります")
    if sim_hz % fps != 0:
        raise ValueError("sim_hz は fps で割り切れる必要があります")
    every = sim_hz // fps
    return int(duration_s * sim_hz), every, int(duration_s * fps)


def ramp_amp(step: int, *, ramp_steps: int = 480, amp: float = 0.25) -> float:
    """歩き始めを滑らかにする振幅ランプ。"""
    if ramp_steps <= 0:
        return amp
    return amp * min(1.0, max(0.0, step / float(ramp_steps)))
