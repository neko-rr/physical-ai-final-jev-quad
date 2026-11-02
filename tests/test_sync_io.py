from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sync_io  # noqa: E402


def test_bootstrap_and_push(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    drive = tmp_path / "drive"
    work = tmp_path / "work"
    monkeypatch.setenv("PAI_DRIVE_ROOT", str(drive))
    monkeypatch.setenv("PAI_WORK_ROOT", str(work))

    run_id = "20261102-0400-go2cat"
    # Drive 側にダミー CKPT と assets
    ckpt = drive / "checkpoints" / "go2" / run_id
    ckpt.mkdir(parents=True)
    (ckpt / "last.txt").write_text("ckpt", encoding="utf-8")
    cat = drive / "assets" / "cat_parts"
    cat.mkdir(parents=True)
    (cat / "ear.obj").write_text("v 0 0 0\n", encoding="utf-8")

    sync_io.bootstrap(run_id)
    assert (work / "assets" / "cat_parts" / "ear.obj").is_file()
    assert (work / "checkpoints" / "go2" / run_id / "last.txt").is_file()

    # work で更新して push
    (work / "checkpoints" / "go2" / run_id / "last.txt").write_text("newer", encoding="utf-8")
    sync_io.push_ckpt(run_id)
    assert (drive / "checkpoints" / "go2" / run_id / "last.txt").read_text(
        encoding="utf-8"
    ) == "newer"

    vid_dir = work / "outputs" / "videos"
    vid_dir.mkdir(parents=True, exist_ok=True)
    (vid_dir / "demo.mp4").write_bytes(b"fake")
    sync_io.push_exports()
    assert (drive / "exports" / "videos" / "demo.mp4").is_file()
