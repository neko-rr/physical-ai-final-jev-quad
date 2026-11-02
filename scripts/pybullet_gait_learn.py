#!/usr/bin/env python3
"""正しい向き（公式スポーン）で Laikago 歩容を山登り学習し Drive へ直書き。

旧 RUN（例: 20261102-0745-pybullet-learn）は触らないこと。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cat_quad.pybullet_gait import (  # noqa: E402
    JOINT_DIRECTIONS,
    JOINT_OFFSETS,
    LEG_PHASE,
    SPAWN_ORN,
    SPAWN_POS,
    apply_joint_map,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID", "pybullet-learn-orn"))
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--forbid-run-id", default="20261102-0745-pybullet-learn")
    args = parser.parse_args(argv)
    if args.run_id == args.forbid_run_id:
        raise SystemExit(f"学習履歴保護: run-id={args.forbid_run_id} は使わないでください")

    try:
        import numpy as np
        import pybullet as p
        import pybullet_data
    except ImportError as exc:
        raise SystemExit("numpy/pybullet が必要です") from exc

    drive = Path(os.environ.get("PAI_DRIVE_ROOT", "/content/drive/MyDrive/pai-final-20261102"))
    out = drive / "checkpoints" / "pybullet" / args.run_id
    out.mkdir(parents=True, exist_ok=True)

    sim_hz = 240

    def targets(step: int, params: dict) -> list[float]:
        w = 2 * np.pi * params["freq"] * step / sim_hz
        motion = [0.0] * 12
        for leg in range(4):
            s = float(np.sin(w + LEG_PHASE[leg]))
            b = leg * 3
            motion[b] = params.get("hip_amp", 0.05) * s
            motion[b + 1] = params["amp"] * s
            motion[b + 2] = -params["amp"] * max(0.0, s)
        return apply_joint_map(motion)

    def rollout(params: dict, steps: int = 240 * 5) -> tuple[float, float, bool]:
        p.connect(p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.8)
        p.setTimeStep(1 / sim_hz)
        p.loadURDF("plane.urdf")
        robot = p.loadURDF(
            "laikago/laikago.urdf",
            list(SPAWN_POS),
            list(SPAWN_ORN),
            flags=p.URDF_USE_SELF_COLLISION,
        )
        stand = apply_joint_map([0.0] * 12)
        for _ in range(240):
            for j, q in enumerate(stand):
                p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=params["force"])
            p.stepSimulation()
        x0 = p.getBasePositionAndOrientation(robot)[0][0]
        fell = False
        for t in range(steps):
            for j, q in enumerate(targets(t, params)):
                p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=params["force"])
            p.stepSimulation()
            if p.getBasePositionAndOrientation(robot)[0][2] < 0.25:
                fell = True
                break
        dx = float(p.getBasePositionAndOrientation(robot)[0][0] - x0)
        p.disconnect()
        return dx - (3.0 if fell else 0.0), dx, fell

    best = {"freq": 1.5, "amp": 0.22, "hip_amp": 0.05, "force": 45.0}
    r_best, _, _ = rollout(best)
    history = [{"iter": 0, "reward": r_best, "params": dict(best)}]
    rng = np.random.default_rng(7)
    for i in range(1, args.iters + 1):
        cand = dict(best)
        cand["freq"] = float(np.clip(best["freq"] + rng.normal() * 0.12, 0.9, 2.4))
        cand["amp"] = float(np.clip(best["amp"] + rng.normal() * 0.05, 0.08, 0.40))
        cand["hip_amp"] = float(np.clip(best["hip_amp"] + rng.normal() * 0.02, 0.0, 0.15))
        cand["force"] = float(np.clip(best["force"] + rng.normal() * 4, 25, 80))
        r, dx, fell = rollout(cand)
        if r > r_best:
            best, r_best = cand, r
            ckpt = {
                "run_id": args.run_id,
                "spawn_orn": list(SPAWN_ORN),
                "reward": r_best,
                "params": best,
                "iter": i,
            }
            (out / "control_ckpt.json").write_text(json.dumps(ckpt, indent=2), encoding="utf-8")
            (out / f"ckpt_iter_{i:03d}.json").write_text(json.dumps(ckpt, indent=2), encoding="utf-8")
        history.append({"iter": i, "reward": r, "dx": dx, "fell": fell, "best_reward": r_best})
        if i % 5 == 0:
            print(f"iter {i} best={r_best:.3f}", flush=True)

    (out / "control_ckpt.json").write_text(
        json.dumps(
            {"run_id": args.run_id, "spawn_orn": list(SPAWN_ORN), "reward": r_best, "params": best},
            indent=2,
        ),
        encoding="utf-8",
    )
    (out / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print("DONE", out, "reward", r_best)
    # 未使用 import の警告回避（directions は apply_joint_map 内）
    _ = (JOINT_DIRECTIONS, JOINT_OFFSETS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
