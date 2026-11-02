from __future__ import annotations

import os
from pathlib import Path

import pytest

from cat_quad.paths import ensure_tree, load_paths


def test_load_paths_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    drive = tmp_path / "drive"
    work = tmp_path / "work"
    monkeypatch.setenv("PAI_DRIVE_ROOT", str(drive))
    monkeypatch.setenv("PAI_WORK_ROOT", str(work))
    paths = load_paths()
    assert paths.drive_root == drive
    assert paths.work_root == work
    assert "go2" in str(paths.drive_checkpoints)
    assert paths.work_genesis.name == "Genesis"


def test_ensure_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAI_DRIVE_ROOT", str(tmp_path / "d"))
    monkeypatch.setenv("PAI_WORK_ROOT", str(tmp_path / "w"))
    paths = load_paths()
    created = ensure_tree(paths)
    assert paths.drive_checkpoints.is_dir()
    assert paths.work_hf_cache.is_dir()
    assert len(created) >= 10


def test_run_id_rejects_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAI_DRIVE_ROOT", str(tmp_path / "d"))
    monkeypatch.setenv("PAI_WORK_ROOT", str(tmp_path / "w"))
    paths = load_paths()
    with pytest.raises(ValueError):
        paths.run_work_ckpt("../evil")
