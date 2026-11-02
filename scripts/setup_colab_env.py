#!/usr/bin/env python3
"""Colab 上で依存とリポジトリ配置を整える。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> int:
    work = Path(os.environ.get("PAI_WORK_ROOT", "/content/pai_work"))
    work.mkdir(parents=True, exist_ok=True)
    repo = work / "repo"
    if not (repo / "scripts" / "train_go2.py").is_file():
        print(f"WARN: {repo} に課題コードがありません。Drive code/repo からコピーしてください。")

    # rsl-rl-lib（Genesis 現行 examples は v5 系）
    run([sys.executable, "-m", "pip", "install", "-q", "rsl-rl-lib>=5.0.0", "tensorboard"])
    run([sys.executable, "-m", "pip", "install", "-q", "genesis-world", "typesafe-sdk>=0.7.5", "Pillow"])

    print("setup_colab_env done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
