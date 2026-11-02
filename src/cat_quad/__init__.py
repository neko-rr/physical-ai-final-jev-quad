"""ネコ型四足デモ用の共有ロジック（PC静的テスト対象）。"""

from .behavior import BehaviorMode, decide_behavior
from .box_util import box_center_normalized, heading_from_box
from .cat_parts import CatPartMeshes, build_cat_parts
from .image_prep import prepare_image_for_jev
from .paths import PaiPaths, ensure_tree, load_paths

__all__ = [
    "BehaviorMode",
    "CatPartMeshes",
    "PaiPaths",
    "box_center_normalized",
    "build_cat_parts",
    "decide_behavior",
    "ensure_tree",
    "heading_from_box",
    "load_paths",
    "prepare_image_for_jev",
]
