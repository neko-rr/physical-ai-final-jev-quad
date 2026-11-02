"""Drive（永続）と /content（高速）のパス設計。

正本の説明はリポジトリ直下 AGENTS.md。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DRIVE_ROOT = "/content/drive/MyDrive/pai-final-20261102"
DEFAULT_WORK_ROOT = "/content/pai_work"


@dataclass(frozen=True)
class PaiPaths:
    """1セッション分のパス束。"""

    drive_root: Path
    work_root: Path

    @property
    def drive_checkpoints(self) -> Path:
        return self.drive_root / "checkpoints" / "go2"

    @property
    def drive_exports_videos(self) -> Path:
        return self.drive_root / "exports" / "videos"

    @property
    def drive_exports_frames(self) -> Path:
        return self.drive_root / "exports" / "frames"

    @property
    def drive_logs(self) -> Path:
        return self.drive_root / "logs" / "go2"

    @property
    def drive_assets(self) -> Path:
        return self.drive_root / "assets"

    @property
    def drive_envs(self) -> Path:
        return self.drive_root / "envs"

    @property
    def drive_hf_cache(self) -> Path:
        return self.drive_envs / "hf-cache"

    @property
    def work_checkpoints(self) -> Path:
        return self.work_root / "checkpoints" / "go2"

    @property
    def work_outputs_videos(self) -> Path:
        return self.work_root / "outputs" / "videos"

    @property
    def work_outputs_frames(self) -> Path:
        return self.work_root / "outputs" / "frames"

    @property
    def work_logs(self) -> Path:
        return self.work_root / "logs"

    @property
    def work_assets(self) -> Path:
        return self.work_root / "assets"

    @property
    def work_hf_cache(self) -> Path:
        return self.work_root / "hf-cache"

    @property
    def work_genesis(self) -> Path:
        return self.work_root / "Genesis"

    @property
    def work_rsl_rl(self) -> Path:
        return self.work_root / "rsl_rl"

    def run_work_ckpt(self, run_id: str) -> Path:
        _validate_run_id(run_id)
        return self.work_checkpoints / run_id

    def run_drive_ckpt(self, run_id: str) -> Path:
        _validate_run_id(run_id)
        return self.drive_checkpoints / run_id


def _validate_run_id(run_id: str) -> None:
    if not run_id or run_id.strip() != run_id:
        raise ValueError("run_id が空、または前後空白があります")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError(f"不正な run_id です: {run_id!r}")


def load_paths(
    *,
    drive_root: str | Path | None = None,
    work_root: str | Path | None = None,
) -> PaiPaths:
    """環境変数 PAI_DRIVE_ROOT / PAI_WORK_ROOT を既定で読む。"""
    drive = Path(
        drive_root
        or os.environ.get("PAI_DRIVE_ROOT", DEFAULT_DRIVE_ROOT)
    )
    work = Path(
        work_root
        or os.environ.get("PAI_WORK_ROOT", DEFAULT_WORK_ROOT)
    )
    return PaiPaths(drive_root=drive, work_root=work)


def ensure_tree(paths: PaiPaths) -> list[Path]:
    """Drive / work の主要ディレクトリを作成し、作った（既存含む）一覧を返す。"""
    targets = [
        paths.drive_root,
        paths.drive_checkpoints,
        paths.drive_exports_videos,
        paths.drive_exports_frames,
        paths.drive_logs,
        paths.drive_assets / "cat_parts",
        paths.drive_assets / "props",
        paths.drive_envs / "pip-wheels",
        paths.drive_hf_cache,
        paths.work_root,
        paths.work_checkpoints,
        paths.work_outputs_videos,
        paths.work_outputs_frames,
        paths.work_logs,
        paths.work_assets,
        paths.work_hf_cache,
    ]
    for path in targets:
        path.mkdir(parents=True, exist_ok=True)
    return targets
