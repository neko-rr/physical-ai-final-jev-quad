from cat_quad.behavior import BehaviorMode, decide_behavior, speed_for


def test_valid_choice() -> None:
    assert decide_behavior("pounce", confidence=0.9) is BehaviorMode.POUNCE


def test_low_confidence_falls_back() -> None:
    assert (
        decide_behavior("sneak", confidence=0.1, min_confidence=0.35)
        is BehaviorMode.WALK
    )


def test_unknown_choice_falls_back() -> None:
    assert decide_behavior("fly") is BehaviorMode.WALK


def test_no_yarn_stops() -> None:
    assert decide_behavior("walk", yarn_visible=False) is BehaviorMode.STOP


def test_speed_stop_is_zero() -> None:
    assert speed_for(BehaviorMode.STOP) == 0.0
    assert speed_for(BehaviorMode.POUNCE) > speed_for(BehaviorMode.SNEAK)
