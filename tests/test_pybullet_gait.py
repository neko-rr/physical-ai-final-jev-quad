"""pybullet_gait の静的テスト（pybullet 不要）。"""

from __future__ import annotations

import math

import pytest

from cat_quad.pybullet_gait import (
    JOINT_OFFSETS,
    SPAWN_ORN,
    apply_joint_map,
    frames_budget,
    standing_targets,
    trot_motion,
    trot_targets,
)


def test_spawn_orn_is_official_not_identity():
    assert SPAWN_ORN == (0.0, 0.5, 0.5, 0.0)
    assert SPAWN_ORN != (0.0, 0.0, 0.0, 1.0)


def test_standing_matches_offsets():
    stand = standing_targets()
    assert len(stand) == 12
    assert stand == list(JOINT_OFFSETS)


def test_apply_joint_map_directions():
    # FR hip direction -1
    out = apply_joint_map([0.2] + [0.0] * 11)
    assert out[0] == pytest.approx(-0.2 + JOINT_OFFSETS[0])


def test_trot_has_four_leg_phases():
    m0 = trot_motion(0)
    assert len(m0) == 12
    # FR(0) と RL(3) は同位相、FL(1) と RR(2) は逆
    # step=0, sin(0)=0, sin(pi)=0 → すべて0付近の thigh
    assert m0[1] == pytest.approx(0.0)
    # 1/4周期で差が出る
    step = int((0.25 / 1.5) * 240)  # freq=1.5
    m = trot_motion(step, freq=1.5, amp=0.25)
    # FR thigh と FL thigh は概ね逆符号
    assert m[1] * m[4] <= 0.0 or abs(m[1]) < 1e-6


def test_trot_targets_length():
    t = trot_targets(10)
    assert len(t) == 12
    assert all(math.isfinite(x) for x in t)


def test_frames_budget_stops_cleanly():
    steps, every, max_frames = frames_budget(60, 30, 240)
    assert steps == 60 * 240
    assert every == 8
    assert max_frames == 1800
    assert steps // every == max_frames


def test_frames_budget_rejects_bad():
    with pytest.raises(ValueError):
        frames_budget(0, 30)
    with pytest.raises(ValueError):
        frames_budget(10, 30, 250)
