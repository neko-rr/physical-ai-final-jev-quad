"""Jev の判定結果を四足の行動モードへ写す。"""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class BehaviorMode(str, Enum):
    """ネコっぽい行動モード（制御側が解釈するラベル）。"""

    SNEAK = "sneak"
    WALK = "walk"
    POUNCE = "pounce"
    STOP = "stop"


# Choice の候補ラベル（英語キー）。Jev criteria と一致させる
VALID_CHOICES = {m.value for m in BehaviorMode}

# コマンド速度の目安（Go2 評価ループで使う想定。単位は相対）
MODE_SPEED: dict[BehaviorMode, float] = {
    BehaviorMode.SNEAK: 0.25,
    BehaviorMode.WALK: 0.6,
    BehaviorMode.POUNCE: 1.0,
    BehaviorMode.STOP: 0.0,
}


def decide_behavior(
    choice: str | None,
    *,
    confidence: float | None = None,
    min_confidence: float = 0.35,
    yarn_visible: bool | None = None,
    fallback: BehaviorMode = BehaviorMode.WALK,
) -> BehaviorMode:
    """Jev Choice と補助フラグから行動を決める。

    - choice が不正 / 低confidence → fallback
    - yarn_visible が False なら STOP（探索は後段で足せる）
    """
    if yarn_visible is False:
        return BehaviorMode.STOP

    if choice is None:
        return fallback

    key = str(choice).strip().lower()
    if key not in VALID_CHOICES:
        return fallback

    if confidence is not None and confidence < min_confidence:
        return fallback

    return BehaviorMode(key)


def speed_for(mode: BehaviorMode) -> float:
    """行動モードに対応する相対速度。"""
    return MODE_SPEED[mode]


def summarize_decision(
    mode: BehaviorMode,
    *,
    choice: str | None = None,
    confidence: float | None = None,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """ログ / レポート用の要約辞書。"""
    out: dict[str, object] = {
        "mode": mode.value,
        "speed": speed_for(mode),
        "raw_choice": choice,
        "confidence": confidence,
    }
    if extra:
        out.update(dict(extra))
    return out
