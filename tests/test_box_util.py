import math

import pytest

from cat_quad.box_util import box_area, box_center_normalized, heading_from_box


def test_center() -> None:
    cx, cy = box_center_normalized(
        {"left": 0.2, "right": 0.4, "top": 0.1, "bottom": 0.5}
    )
    assert cx == pytest.approx(0.3)
    assert cy == pytest.approx(0.3)


def test_heading_left_is_positive() -> None:
    yaw = heading_from_box(
        {"left": 0.0, "right": 0.2, "top": 0.4, "bottom": 0.6},
        max_yaw_rad=math.radians(45),
    )
    assert yaw > 0


def test_area() -> None:
    assert box_area({"left": 0.0, "right": 0.5, "top": 0.0, "bottom": 0.5}) == pytest.approx(
        0.25
    )


def test_invalid_box() -> None:
    with pytest.raises(ValueError):
        box_center_normalized({"left": 0.8, "right": 0.2, "top": 0.1, "bottom": 0.2})
