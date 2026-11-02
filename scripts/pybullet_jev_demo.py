#!/usr/bin/env python3
"""提出用正本: 正しい向きの Laikago + 毛糸玉 + Jev 行動切替（Drive直書き）。

- 動画は **60秒以上**（default 75秒）
- 転倒時は即リセットして録画継続（ひっくり返り映像を伸ばさない）
- 数秒ごとにカメラ画像を Jev へ渡し、sneak/walk/pounce/stop で歩容を切替
- 旧 RUN（向き誤り学習 0745 等）の履歴は触らない
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cat_quad.behavior import BehaviorMode, speed_for  # noqa: E402
from cat_quad.pybullet_gait import (  # noqa: E402
    LEG_PHASE,
    SPAWN_ORN,
    SPAWN_POS,
    apply_joint_map,
)


def _targets(step: int, *, freq: float, amp: float, hip_amp: float) -> list[float]:
    w = 2 * math.pi * freq * step / 240.0
    motion = [0.0] * 12
    for leg in range(4):
        s = math.sin(w + LEG_PHASE[leg])
        b = leg * 3
        motion[b] = hip_amp * s
        motion[b + 1] = amp * s
        motion[b + 2] = -amp * max(0.0, s)
    return apply_joint_map(motion)


def _mode_params(mode: BehaviorMode, base: dict) -> dict:
    sp = speed_for(mode)
    if mode == BehaviorMode.STOP:
        return {**base, "amp": 0.0, "freq": base["freq"], "hip_amp": 0.0}
    if mode == BehaviorMode.SNEAK:
        return {**base, "amp": base["amp"] * 0.55, "freq": base["freq"] * 0.7, "hip_amp": base["hip_amp"] * 0.5}
    if mode == BehaviorMode.POUNCE:
        return {**base, "amp": min(0.38, base["amp"] * 1.35), "freq": base["freq"] * 1.35, "hip_amp": base["hip_amp"]}
    return dict(base) | {"amp": base["amp"] * (0.7 + 0.5 * sp)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="20261102-jev-demo")
    parser.add_argument("--duration-s", type=float, default=75.0, help="課題要件のため60秒以上")
    parser.add_argument("--jev-every-s", type=float, default=2.0, help="何秒ごとに Jev するか")
    parser.add_argument(
        "--forbid-run-id",
        default="20261102-0745-pybullet-learn",
    )
    parser.add_argument("--no-jev", action="store_true", help="API無しでモードを周期切替（デバッグ）")
    args = parser.parse_args(argv)
    if args.duration_s < 60.0:
        raise SystemExit("課題要件: --duration-s は 60 以上にしてください")
    if args.run_id == args.forbid_run_id:
        raise SystemExit("学習履歴保護: この run-id は禁止")

    import pybullet as p
    import pybullet_data
    from PIL import Image, ImageDraw
    import imageio.v2 as imageio

    drive = Path(os.environ.get("PAI_DRIVE_ROOT", "/content/drive/MyDrive/pai-final-20261102"))
    work = Path(os.environ.get("PAI_WORK_ROOT", "/content/pai_work"))
    ckpt_dir = drive / "checkpoints" / "pybullet" / args.run_id
    frames_dir = work / "outputs" / "frames" / args.run_id
    vid_drive = drive / "exports" / "videos" / f"{args.run_id}.mp4"
    vid_work = work / "outputs" / "videos" / f"{args.run_id}.mp4"
    log_path = drive / "logs" / f"{args.run_id}_jev.json"
    for d in [ckpt_dir, frames_dir, vid_work.parent, vid_drive.parent, log_path.parent]:
        d.mkdir(parents=True, exist_ok=True)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    base = {"freq": 1.45, "amp": 0.20, "hip_amp": 0.04, "force": 50.0}
    # 可能なら直前の正しい向き学習を読む（0745は読まない）
    orn_ckpt = drive / "checkpoints" / "pybullet" / "20261102-0822-pybullet-learn-orn" / "control_ckpt.json"
    if orn_ckpt.is_file():
        data = json.loads(orn_ckpt.read_text(encoding="utf-8"))
        if data.get("params"):
            base.update({k: float(v) for k, v in data["params"].items() if k in base or k == "force"})

    client = None
    if not args.no_jev:
        from cat_quad.jev_vision import analyze_frame, build_live_client

        os.environ.setdefault("TYPESAFE_API_KEY", "")
        client = build_live_client()

    p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.8)
    p.setTimeStep(1 / 240)
    p.loadURDF("plane.urdf")
    robot = p.loadURDF(
        "laikago/laikago.urdf",
        list(SPAWN_POS),
        list(SPAWN_ORN),
        flags=p.URDF_USE_SELF_COLLISION,
    )
    # 毛糸玉（赤い球）を前方に置く → Jev の視覚ターゲット
    yarn = p.createVisualShape(p.GEOM_SPHERE, radius=0.06, rgbaColor=[1, 0.15, 0.1, 1])
    yarn_col = p.createCollisionShape(p.GEOM_SPHERE, radius=0.06)
    yarn_id = p.createMultiBody(0.05, yarn_col, yarn, [0.9, 0.0, 0.06])

    stand = apply_joint_map([0.0] * 12)
    for _ in range(360):
        for j, q in enumerate(stand):
            p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=base["force"])
        p.stepSimulation()

    fps = 30
    every = 8
    max_frames = int(args.duration_s * fps)
    steps = int(args.duration_s * 240)
    jev_every_steps = int(args.jev_every_s * 240)
    mode = BehaviorMode.WALK
    params = _mode_params(mode, base)
    jev_log: list[dict] = []
    fall_streak = 0
    fall_resets = 0
    n_saved = 0
    w, h = 640, 480

    for t in range(steps):
        if t % jev_every_steps == 0 and n_saved > 0:
            # 直近フレームで Jev（またはデモ用サイクル）
            last = frames_dir / f"frame_{n_saved-1:05d}.jpg"
            if client is not None and last.is_file():
                try:
                    d = analyze_frame(client, last, prepared_dir=work / "outputs" / "frames" / f"{args.run_id}_jev")
                    mode = d.mode
                    jev_log.append(
                        {
                            "t": t,
                            "frame": last.name,
                            "mode": mode.value,
                            "choice": d.choice,
                            "confidence": d.confidence,
                            "box": d.box,
                        }
                    )
                except Exception as exc:  # 業務: Jev失敗時は walk 継続
                    jev_log.append({"t": t, "error": type(exc).__name__, "msg": str(exc)[:160]})
                    mode = BehaviorMode.WALK
            else:
                cycle = [BehaviorMode.WALK, BehaviorMode.SNEAK, BehaviorMode.POUNCE, BehaviorMode.STOP]
                mode = cycle[(t // jev_every_steps) % len(cycle)]
                jev_log.append({"t": t, "mode": mode.value, "synthetic": True})
            params = _mode_params(mode, base)

        for j, q in enumerate(_targets(t, freq=params["freq"], amp=params["amp"], hip_amp=params["hip_amp"])):
            p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=params.get("force", 50))
        # 毛糸玉をゆっくり手前へ（追跡対象が動く）
        if t % 24 == 0:
            p.resetBasePositionAndOrientation(
                yarn_id,
                [0.9 - 0.0005 * t, 0.15 * math.sin(0.002 * t), 0.06],
                [0, 0, 0, 1],
            )
        p.stepSimulation()
        pos, orn = p.getBasePositionAndOrientation(robot)
        # 転倒したら即リセットして録画は60秒以上まで継続（ひっくり返り映像を伸ばさない）
        if pos[2] < 0.28:
            fall_streak += 1
            fall_resets += 1
            p.resetBasePositionAndOrientation(robot, [pos[0], 0.0, 0.50], list(SPAWN_ORN))
            p.resetBaseVelocity(robot, [0.08, 0.0, 0.0], [0.0, 0.0, 0.0])
            stand_now = apply_joint_map([0.0] * 12)
            for j, q in enumerate(stand_now):
                p.resetJointState(robot, j, q)
        else:
            fall_streak = 0

        if t % every == 0:
            view = p.computeViewMatrixFromYawPitchRoll([pos[0], pos[1], 0.38], 2.6, 25, -16, 0, 2)
            proj = p.computeProjectionMatrixFOV(55, w / h, 0.1, 20)
            _, _, rgb, _, _ = p.getCameraImage(w, h, view, proj, renderer=p.ER_TINY_RENDERER)
            rgb = np.reshape(rgb, (h, w, 4))[:, :, :3].astype(np.uint8)
            img = Image.fromarray(rgb)
            draw = ImageDraw.Draw(img)
            draw.rectangle((8, 8, 280, 48), fill=(0, 0, 0))
            draw.text((16, 16), f"Jev mode: {mode.value}", fill=(0, 255, 120))
            fp = frames_dir / f"frame_{n_saved:05d}.jpg"
            img.save(fp, quality=85)
            n_saved += 1
            if n_saved % 150 == 0:
                print(f"frames {n_saved}/{max_frames} mode={mode.value}", flush=True)
            if n_saved >= max_frames:
                break

    p.disconnect()
    (ckpt_dir / "control_ckpt.json").write_text(
        json.dumps(
            {
                "run_id": args.run_id,
                "spawn_orn": list(SPAWN_ORN),
                "base_params": base,
                "jev_calls": len(jev_log),
                "frames": n_saved,
                "duration_s_target": args.duration_s,
                "falls_reset": fall_resets,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log_path.write_text(json.dumps(jev_log, ensure_ascii=False, indent=2), encoding="utf-8")

    files = sorted(frames_dir.glob("frame_*.jpg"))
    with imageio.get_writer(str(vid_work), fps=fps, codec="libx264", quality=8) as wr:
        for fp in files:
            wr.append_data(imageio.imread(fp))
    shutil.copy2(vid_work, vid_drive)
    duration_s = len(files) / fps
    if duration_s < 60.0:
        raise SystemExit(f"課題要件未達: 動画が {duration_s:.1f}s（60秒未満）")
    print("VIDEO", vid_drive, "sec", duration_s, "jev_events", len(jev_log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
