"""Jev Box 回答（正規化座標）の幾何ユーティリティ。"""

from __future__ import annotations

import math
from typing import Mapping


def _edge(box: Mapping[str, float], key: str) -> float:
    if key not in box:
        raise KeyError(f"Box に '{key}' がありません: {list(box)}")
    value = float(box[key])
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Box '{key}' は 0..1 である必要があります: {value}")
    return value


def box_center_normalized(box: Mapping[str, float]) -> tuple[float, float]:
    """(cx, cy) を画像正規化座標で返す。原点は左上、y は下向き。"""
    left = _edge(box, "left")
    right = _edge(box, "right")
    top = _edge(box, "top")
    bottom = _edge(box, "bottom")
    if right < left or bottom < top:
        raise ValueError(f"不正な Box です: {dict(box)}")
    return (left + right) / 2.0, (top + bottom) / 2.0


def heading_from_box(
    box: Mapping[str, float],
    *,
    image_center_x: float = 0.5,
    max_yaw_rad: float = math.radians(45.0),
) -> float:
    """箱中心が画像中央からどれだけ横ずれしているかを yaw に写す。

    cx < 0.5 → 左（正の yaw とみなす簡易規約）
    戻り値は [-max_yaw_rad, +max_yaw_rad]
    """
    cx, _cy = box_center_normalized(box)
    # 中央=0、左端=-1、右端=+1
    offset = (cx - image_center_x) / max(image_center_x, 1e-6)
    offset = max(-1.0, min(1.0, offset))
    # 左に見えている対象へ向く → 負オフセットで正 yaw（簡易）
    return float(-offset * max_yaw_rad)


def box_area(box: Mapping[str, float]) -> float:
    """正規化面積 (0..1)。近い対象ほど大きい想定。"""
    left = _edge(box, "left")
    right = _edge(box, "right")
    top = _edge(box, "top")
    bottom = _edge(box, "bottom")
    return max(0.0, (right - left) * (bottom - top))
