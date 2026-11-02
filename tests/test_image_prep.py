from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from cat_quad.image_prep import MAX_SIDE, MIN_SIDE, prepare_image_for_jev


def test_prepare_shrinks_large_image(tmp_path: Path) -> None:
    src = tmp_path / "big.png"
    Image.new("RGB", (3000, 2000), (10, 20, 30)).save(src)
    out = prepare_image_for_jev(src, output_path=tmp_path / "out.jpg")
    assert isinstance(out, Path)
    with Image.open(out) as img:
        assert max(img.size) <= MAX_SIDE
        assert min(img.size) >= MIN_SIDE


def test_prepare_pads_tiny_image(tmp_path: Path) -> None:
    src = tmp_path / "tiny.png"
    Image.new("RGB", (64, 48), (1, 2, 3)).save(src)
    out = prepare_image_for_jev(src, output_path=tmp_path / "pad.jpg")
    with Image.open(out) as img:
        assert img.size[0] >= MIN_SIDE
        assert img.size[1] >= MIN_SIDE


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        prepare_image_for_jev(tmp_path / "nope.jpg")
