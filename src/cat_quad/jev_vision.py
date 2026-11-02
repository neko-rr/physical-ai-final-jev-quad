"""Jev 画像診断ラッパ（System One + Danger Zone Images）。

実 API 呼び出しは Colab / 実行時のみ。単体テストは FakeClient を注入する。
キーは環境変数 TYPESAFE_API_KEY（ログに出さない）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from .behavior import BehaviorMode, decide_behavior
from .box_util import box_area, box_center_normalized, heading_from_box
from .image_prep import prepare_image_for_jev

IMAGE_HEADER = {"TypeSafe-Danger-Zone-Images": "true"}
DEFAULT_MODEL = "jev-1.14.0"

ACTION_CRITERIA = {
    "sneak": "Quiet crouched approach, like a cat stalking.",
    "walk": "Calm walking toward the target.",
    "pounce": "Short sudden dash toward a nearby toy.",
    "stop": "Stay still and observe.",
}


class SystemOneClient(Protocol):
    """typesafe_sdk.TypeSafeClient 互換の最小面。"""

    def system_one(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class VisionDecision:
    """1フレーム分の画像判定結果。"""

    mode: BehaviorMode
    choice: str | None
    confidence: float | None
    box: dict[str, float] | None
    yarn_center: tuple[float, float] | None
    yaw_rad: float
    yarn_area: float
    raw_answers: Mapping[str, Any]


def _require_api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "TYPESAFE_API_KEY が未設定です。.env または Colab Secrets から渡してください。"
        )
    return key


def build_live_client(model: str = DEFAULT_MODEL) -> Any:
    """本番用クライアント。typesafe-sdk が必要。キー有無だけ先に検査する。"""
    _require_api_key()
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError as exc:
        raise RuntimeError(
            "typesafe-sdk がありません。pip install 'typesafe-sdk>=0.7.5' を実行してください。"
        ) from exc
    # model は各リクエストで渡す。ここでは接続用オブジェクトのみ
    return TypeSafeClient()


def analyze_frame(
    client: SystemOneClient,
    image_path: Path,
    *,
    model: str = DEFAULT_MODEL,
    prepared_dir: Path | None = None,
    min_confidence: float = 0.35,
) -> VisionDecision:
    """カメラ画像を Jev に渡し、行動モードと毛糸玉 Box を返す。

    client.system_one の戻りは SDK 互換を想定:
      result.answers['action'].choice / .confidence
      result.answers['yarn_box'].box に left/right/top/bottom
    FakeClient では dict でも可（下の _read_* が吸収）。
    """
    if not image_path.is_file():
        raise FileNotFoundError(f"画像がありません: {image_path}")

    out_path = None
    if prepared_dir is not None:
        prepared_dir.mkdir(parents=True, exist_ok=True)
        out_path = prepared_dir / f"jev_{image_path.stem}.jpg"
    prepared = prepare_image_for_jev(image_path, output_path=out_path)
    if not isinstance(prepared, Path):
        raise TypeError("output_path 指定時は Path が返る想定です")

    # SDK が無い環境でも Fake で通るよう、Image は遅延 import
    try:
        from typesafe_sdk import Box, Choice, Image
    except ImportError:
        Box = Choice = Image = None  # type: ignore

    if Image is not None and Box is not None and Choice is not None:
        state = {"frame": Image(prepared)}
        questions = {
            "yarn_box": Box(instructions="the yarn ball or small toy in `frame`"),
            "action": Choice(
                instructions=(
                    "Looking at `frame`, which cat-like action should a quadruped robot take "
                    "toward the toy?"
                ),
                criteria=ACTION_CRITERIA,
            ),
        }
        result = client.system_one(
            model=model,
            state=state,
            questions=questions,
            extra_headers=IMAGE_HEADER,
        )
        answers = _as_mapping(getattr(result, "answers", result))
    else:
        # 静的テスト用: FakeClient が path 文字列だけ受け取る
        result = client.system_one(
            model=model,
            state={"frame_path": str(prepared)},
            questions={"yarn_box": "box", "action": "choice"},
            extra_headers=IMAGE_HEADER,
        )
        answers = _as_mapping(getattr(result, "answers", result))

    choice, conf = _read_choice(answers.get("action"))
    box = _read_box(answers.get("yarn_box"))
    yarn_visible = box is not None and box_area(box) > 1e-4
    mode = decide_behavior(
        choice,
        confidence=conf,
        min_confidence=min_confidence,
        yarn_visible=yarn_visible if box is not None else None,
    )
    center = box_center_normalized(box) if box else None
    yaw = heading_from_box(box) if box else 0.0
    area = box_area(box) if box else 0.0
    return VisionDecision(
        mode=mode,
        choice=choice,
        confidence=conf,
        box=box,
        yarn_center=center,
        yaw_rad=yaw,
        yarn_area=area,
        raw_answers=answers,
    )


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    # SDK オブジェクトの場合
    if hasattr(value, "items"):
        return dict(value.items())  # type: ignore[arg-type]
    raise TypeError(f"answers を Mapping にできません: {type(value)}")


def _read_choice(answer: Any) -> tuple[str | None, float | None]:
    if answer is None:
        return None, None
    if isinstance(answer, Mapping):
        return (
            answer.get("choice"),
            float(answer["confidence"]) if answer.get("confidence") is not None else None,
        )
    choice = getattr(answer, "choice", None)
    conf = getattr(answer, "confidence", None)
    return choice, float(conf) if conf is not None else None


def _read_box(answer: Any) -> dict[str, float] | None:
    if answer is None:
        return None
    raw = answer
    if not isinstance(answer, Mapping):
        raw = getattr(answer, "box", None) or getattr(answer, "coordinates", None) or answer
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        # dataclass BoxCoordinates
        raw = {
            "left": getattr(raw, "left"),
            "right": getattr(raw, "right"),
            "top": getattr(raw, "top"),
            "bottom": getattr(raw, "bottom"),
        }
    return {
        "left": float(raw["left"]),
        "right": float(raw["right"]),
        "top": float(raw["top"]),
        "bottom": float(raw["bottom"]),
    }
