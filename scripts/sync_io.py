#!/usr/bin/env python3
"""Drive ↔ /content の同期ヘルパ。

学習は /content（work）へ書き、定期的に Drive へ押し込む。
Colab でも PC の一時ディレクトリでも同じ API。

例:
  python scripts/sync_io.py bootstrap --run-id 20261102-0400-go2cat
  python scripts/sync_io.py push-ckpt --run-id 20261102-0400-go2cat
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cat_quad.paths import ensure_tree, load_paths  # noqa: E402


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def bootstrap(run_id: str | None = None) -> None:
    """ディレクトリ作成 + Drive 上の assets/ckpt を work へ（あれば）。"""
    paths = load_paths()
    ensure_tree(paths)

    # 資産: Drive → work
    drive_cat = paths.drive_assets / "cat_parts"
    if drive_cat.exists() and any(drive_cat.iterdir()):
        _copy_tree(drive_cat, paths.work_assets / "cat_parts")

    if run_id:
        drive_ckpt = paths.run_drive_ckpt(run_id)
        if drive_ckpt.exists() and any(drive_ckpt.iterdir()):
            _copy_tree(drive_ckpt, paths.run_work_ckpt(run_id))

    # HF キャッシュ: Drive → work（大きいので存在時のみ）
    if paths.drive_hf_cache.exists() and any(paths.drive_hf_cache.iterdir()):
        # 丸ごと copytree は重いので、空の work だけのとき同期
        if not any(paths.work_hf_cache.iterdir()):
            _copy_tree(paths.drive_hf_cache, paths.work_hf_cache)

    print(f"bootstrap OK drive={paths.drive_root} work={paths.work_root}")


def push_ckpt(run_id: str) -> None:
    """work の CKPT を Drive へ。"""
    paths = load_paths()
    ensure_tree(paths)
    src = paths.run_work_ckpt(run_id)
    if not src.exists():
        raise FileNotFoundError(f"work CKPT がありません: {src}")
    dst = paths.run_drive_ckpt(run_id)
    _copy_tree(src, dst)
    print(f"push-ckpt OK {src} -> {dst}")


def push_exports() -> None:
    """動画・フレーム・ログを Drive exports / logs へ。"""
    paths = load_paths()
    ensure_tree(paths)
    for src_dir, dst_dir in (
        (paths.work_outputs_videos, paths.drive_exports_videos),
        (paths.work_outputs_frames, paths.drive_exports_frames),
        (paths.work_logs, paths.drive_logs / "session"),
    ):
        if not src_dir.exists():
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.iterdir():
            target = dst_dir / item.name
            if item.is_dir():
                _copy_tree(item, target)
            else:
                shutil.copy2(item, target)
    print("push-exports OK")


def push_hf_cache() -> None:
    """HF キャッシュを Drive へ退避（切断対策）。"""
    paths = load_paths()
    ensure_tree(paths)
    if not paths.work_hf_cache.exists() or not any(paths.work_hf_cache.iterdir()):
        print("push-hf-cache skip (empty)")
        return
    _copy_tree(paths.work_hf_cache, paths.drive_hf_cache)
    print(f"push-hf-cache OK -> {paths.drive_hf_cache}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PAI Drive↔content sync")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_boot = sub.add_parser("bootstrap", help="ディレクトリ作成と Drive→work")
    p_boot.add_argument("--run-id", default=None)

    p_ckpt = sub.add_parser("push-ckpt", help="CKPT を Drive へ")
    p_ckpt.add_argument("--run-id", required=True)

    sub.add_parser("push-exports", help="動画・フレーム・ログを Drive へ")
    sub.add_parser("push-hf-cache", help="HF キャッシュを Drive へ")

    args = parser.parse_args(argv)
    if args.cmd == "bootstrap":
        bootstrap(args.run_id)
    elif args.cmd == "push-ckpt":
        push_ckpt(args.run_id)
    elif args.cmd == "push-exports":
        push_exports()
    elif args.cmd == "push-hf-cache":
        push_hf_cache()
    else:
        parser.error(f"unknown cmd: {args.cmd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
