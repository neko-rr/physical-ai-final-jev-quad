#!/usr/bin/env python3
"""Laikago の立位→トロット録画（公式スポーン姿勢準拠）。

Drive 直書き対応。Genesis 不可時の提出用デモ。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from cat_quad.pybullet_gait import (  # noqa: E402
    SPAWN_ORN,
    SPAWN_POS,
    frames_budget,
    ramp_amp,
    standing_targets,
    trot_targets,
)
from cat_quad.paths import ensure_tree, load_paths  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PyBullet laikago walk record")
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID", "pybullet-walk"))
    parser.add_argument("--duration-s", type=float, default=60.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--freq", type=float, default=1.5)
    parser.add_argument("--amp", type=float, default=0.25)
    parser.add_argument("--force", type=float, default=40.0)
    parser.add_argument("--settle-steps", type=int, default=480, help="録画前の立位安定化")
    parser.add_argument("--log-to-drive", action="store_true")
    args = parser.parse_args(argv)

    try:
        import pybullet as p
        import pybullet_data
        from PIL import Image
        import imageio.v2 as imageio
    except ImportError as exc:
        raise SystemExit("pybullet / Pillow / imageio が必要です") from exc

    paths = load_paths()
    ensure_tree(paths)
    steps, every, max_frames = frames_budget(args.duration_s, args.fps)

    ckpt_dir = paths.drive_root / "checkpoints" / "pybullet" / args.run_id
    frames_dir = paths.work_outputs_frames / args.run_id
    vid_work = paths.work_outputs_videos / f"{args.run_id}.mp4"
    vid_drive = paths.drive_exports_videos / f"{args.run_id}.mp4"
    for d in [ckpt_dir, frames_dir, paths.work_outputs_videos, paths.drive_exports_videos]:
        d.mkdir(parents=True, exist_ok=True)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    ckpt = {
        "run_id": args.run_id,
        "backend": "pybullet",
        "urdf": "laikago/laikago.urdf",
        "spawn_pos": list(SPAWN_POS),
        "spawn_orn": list(SPAWN_ORN),
        "note": "official spawn orn [0,0.5,0.5,0]; identity quat makes robot look vertical",
        "duration_s": args.duration_s,
        "fps": args.fps,
        "freq": args.freq,
        "amp": args.amp,
    }
    (ckpt_dir / "control_ckpt.json").write_text(json.dumps(ckpt, indent=2), encoding="utf-8")

    cid = p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.8)
    p.setTimeStep(1.0 / 240.0)
    p.loadURDF("plane.urdf")
    # ★公式どおりの向き（ここを単位クォータニオンにすると縦になる）
    robot = p.loadURDF(
        "laikago/laikago.urdf",
        list(SPAWN_POS),
        list(SPAWN_ORN),
        flags=p.URDF_USE_SELF_COLLISION,
    )
    for j in range(p.getNumJoints(robot)):
        p.changeDynamics(robot, j, linearDamping=0, angularDamping=0)

    stand = standing_targets()
    for _ in range(args.settle_steps):
        for j, q in enumerate(stand):
            p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=args.force)
        p.stepSimulation()

    w, h = 640, 480
    n_saved = 0
    for t in range(steps):
        amp = ramp_amp(t, ramp_steps=480, amp=args.amp)
        targets = trot_targets(t, freq=args.freq, amp=amp)
        for j, q in enumerate(targets):
            p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=args.force)
        p.stepSimulation()
        pos, _ = p.getBasePositionAndOrientation(robot)
        if t % every == 0:
            view = p.computeViewMatrixFromYawPitchRoll(
                [pos[0], pos[1], 0.35], 2.8, 35 + 0.01 * t, -20, 0, 2
            )
            proj = p.computeProjectionMatrixFOV(55, w / h, 0.1, 20)
            _, _, rgb, _, _ = p.getCameraImage(w, h, view, proj, renderer=p.ER_TINY_RENDERER)
            rgb = np.reshape(rgb, (h, w, 4))[:, :, :3].astype(np.uint8)
            Image.fromarray(rgb).save(frames_dir / f"frame_{n_saved:05d}.jpg", quality=85)
            n_saved += 1
            if n_saved % 300 == 0:
                print(f"frames {n_saved}/{max_frames} x={pos[0]:.2f}", flush=True)
            if n_saved >= max_frames:
                break
    p.disconnect()

    files = sorted(frames_dir.glob("frame_*.jpg"))
    print("encode", len(files), flush=True)
    with imageio.get_writer(str(vid_work), fps=args.fps, codec="libx264", quality=8) as writer:
        for fp in files:
            writer.append_data(imageio.imread(fp))
    # 提出用は常に Drive へ（切断対策）
    shutil.copy2(vid_work, vid_drive)
    print("DRIVE", vid_drive, vid_drive.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
