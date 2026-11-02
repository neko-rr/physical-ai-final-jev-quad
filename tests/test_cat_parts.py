from pathlib import Path

from cat_quad.cat_parts import build_cat_parts, export_cat_parts, write_obj


def test_build_has_triangles() -> None:
    parts = build_cat_parts()
    assert parts.left_ear.faces.ndim == 2
    assert parts.left_ear.faces.shape[1] == 3
    assert parts.tail.vertices.shape[1] == 3
    assert len(parts.left_ear.vertices) > 0
    # 左右で X 符号が分かれる
    assert parts.left_ear.vertices[:, 0].mean() < 0
    assert parts.right_ear.vertices[:, 0].mean() > 0


def test_export_obj(tmp_path: Path) -> None:
    paths = export_cat_parts(tmp_path)
    assert set(paths) == {"left_ear", "right_ear", "tail"}
    for p in paths.values():
        text = p.read_text(encoding="utf-8")
        assert text.startswith("#")
        assert "\nv " in text or text.count("\nv ") >= 0
        assert "v " in text
        assert "f " in text


def test_write_obj_extension(tmp_path: Path) -> None:
    parts = build_cat_parts()
    try:
        write_obj(parts.tail, tmp_path / "tail.stl")
        raised = False
    except ValueError:
        raised = True
    assert raised
