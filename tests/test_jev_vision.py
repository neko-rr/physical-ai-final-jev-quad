from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from cat_quad.behavior import BehaviorMode
from cat_quad.jev_vision import VisionDecision, analyze_frame


class FakeClient:
    """typesafe-sdk 無しで analyze_frame を通す。"""

    def __init__(self, answers: dict) -> None:
        self.answers = answers
        self.last_kwargs: dict | None = None

    def system_one(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(answers=self.answers)


def _make_frame(path: Path) -> Path:
    Image.new("RGB", (640, 480), (200, 180, 160)).save(path)
    return path


def test_analyze_frame_pounce(tmp_path: Path) -> None:
    frame = _make_frame(tmp_path / "cam.png")
    client = FakeClient(
        {
            "action": {"choice": "pounce", "confidence": 0.88},
            "yarn_box": {
                "left": 0.55,
                "right": 0.75,
                "top": 0.40,
                "bottom": 0.60,
            },
        }
    )
    decision = analyze_frame(client, frame, prepared_dir=tmp_path / "prep")
    assert isinstance(decision, VisionDecision)
    assert decision.mode is BehaviorMode.POUNCE
    assert decision.box is not None
    assert decision.yarn_center is not None
    assert client.last_kwargs is not None
    assert client.last_kwargs["extra_headers"]["TypeSafe-Danger-Zone-Images"] == "true"


def test_analyze_frame_stop_when_tiny_box(tmp_path: Path) -> None:
    frame = _make_frame(tmp_path / "cam2.png")
    client = FakeClient(
        {
            "action": {"choice": "walk", "confidence": 0.9},
            "yarn_box": {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0},
        }
    )
    decision = analyze_frame(client, frame, prepared_dir=tmp_path / "prep")
    # 面積ほぼ0 → yarn_visible False → STOP
    assert decision.mode is BehaviorMode.STOP
