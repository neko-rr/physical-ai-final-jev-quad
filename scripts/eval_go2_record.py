#!/usr/bin/env python3
"""学習済み Go2 を headless 録画する（ネコ耳尻尾付き・提出動画用）。

- CKPT は work の checkpoints/go2/<run_id>
- 動画・フレームは work/outputs へ書き、任意で Drive 同期
- --with-jev で数フレームごとに Jev 画像診断し指令速度を切替
"""

from __future__ import annotations

import argparse
import os
import pickle
import shutil
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SRC))

from cat_quad.behavior import BehaviorMode, speed_for  # noqa: E402
from cat_quad.cat_parts import export_cat_parts  # noqa: E402
from cat_quad.paths import ensure_tree, load_paths  # noqa: E402
from go2_env import Go2Env  # noqa: E402


def _require_rsl() -> None:
    try:
        if int(metadata.version("rsl-rl-lib").split(".")[0]) < 5:
            raise ImportError
    except (metadata.PackageNotFoundError, ImportError, ValueError) as exc:
        raise ImportError("pip install 'rsl-rl-lib>=5.0.0' が必要です") from exc


def _attach_cat_parts(scene, robot, parts_dir: Path) -> None:
    """耳・尻尾 OBJ をロボット近傍に置く（見た目用。制御には使わない）。"""
    import genesis as gs

    # 初期位置の頭・尻あたりに固定オフセット（簡易）
    base = np.array(robot.get_pos().detach().cpu().numpy()[0], dtype=np.float64)
    placements = {
        "cat_left_ear.obj": base + np.array([-0.03, 0.18, 0.12]),
        "cat_right_ear.obj": base + np.array([0.03, 0.18, 0.12]),
        "cat_tail.obj": base + np.array([0.0, -0.25, 0.05]),
    }
    for name, pos in placements.items():
        path = parts_dir / name
        if not path.is_file():
            continue
        scene.add_entity(
            gs.morphs.Mesh(file=str(path), scale=1.0, pos=pos.tolist()),
        )


def main(argv: list[str] | None = None) -> int:
    _require_rsl()
    from rsl_rl.runners import OnPolicyRunner

    import genesis as gs

    parser = argparse.ArgumentParser(description="Eval + record Go2 cat demo")
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID", "20261102-0400-go2cat"))
    parser.add_argument("--ckpt", type=int, default=100, help="model_{ckpt}.pt の番号")
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--with-jev", action="store_true")
    parser.add_argument("--jev-every", type=int, default=60, help="何ステップごとに Jev するか")
    parser.add_argument("--sync-drive", action="store_true")
    args = parser.parse_args(argv)

    paths = load_paths()
    ensure_tree(paths)
    log_dir = paths.run_work_ckpt(args.run_id)
    cfg_path = log_dir / "cfgs.pkl"
    ckpt_path = log_dir / f"model_{args.ckpt}.pt"
    if not cfg_path.is_file() or not ckpt_path.is_file():
        raise FileNotFoundError(f"CKPT がありません: {log_dir} (need cfgs.pkl and model_{args.ckpt}.pt)")

    parts_dir = paths.work_assets / "cat_parts"
    export_cat_parts(parts_dir)
    export_cat_parts(paths.drive_assets / "cat_parts")

    with open(cfg_path, "rb") as f:
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(f)
    reward_cfg["reward_scales"] = {}

    frames_dir = paths.work_outputs_frames / args.run_id
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    video_path = paths.work_outputs_videos / f"{args.run_id}.mp4"

    gs.init(backend=gs.gpu, precision="32", logging_level="warning")
    # headless 録画用シーンは Go2Env 内。カメラを追加するために env 生成後に取得する
    env = Go2Env(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=False,
    )
    try:
        _attach_cat_parts(env.scene, env.robot, parts_dir)
    except Exception as exc:  # 見た目失敗でも歩行は続行
        print(f"cat parts attach skipped: {exc}")

    cam = env.scene.add_camera(
        res=(640, 480),
        pos=(2.5, 0.0, 1.8),
        lookat=(0.0, 0.0, 0.35),
        fov=40,
        GUI=False,
    )

    runner = OnPolicyRunner(env, train_cfg, str(log_dir), device=gs.device)
    runner.load(str(ckpt_path))
    policy = runner.get_inference_policy(device=gs.device)

    jev_client = None
    if args.with_jev:
        from cat_quad.jev_vision import analyze_frame, build_live_client

        jev_client = build_live_client()

    obs_dict = env.reset()
    mode = BehaviorMode.WALK
    env.set_command_velocities(speed_for(mode), 0.0, 0.0)

    cam.start_recording()
    decision_log: list[dict] = []
    with __import__("torch").no_grad():
        for step in range(args.steps):
            actions = policy(obs_dict)
            obs_dict, _rews, _dones, _infos = env.step(actions)
            rgb, *_rest = cam.render(rgb=True)
            frame = np.asarray(rgb)
            if frame.dtype != np.uint8:
                frame = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
            frame_path = frames_dir / f"frame_{step:04d}.jpg"
            PILImage.fromarray(frame).save(frame_path, quality=90)

            if jev_client is not None and step % max(1, args.jev_every) == 0:
                try:
                    decision = analyze_frame(
                        jev_client,
                        frame_path,
                        prepared_dir=frames_dir / "jev_prep",
                    )
                    mode = decision.mode
                    lin = speed_for(mode)
                    yaw = float(decision.yaw_rad) * 0.5
                    env.set_command_velocities(lin, 0.0, yaw)
                    decision_log.append(
                        {
                            "step": step,
                            "mode": mode.value,
                            "yaw": yaw,
                            "confidence": decision.confidence,
                        }
                    )
                    print(f"step={step} jev mode={mode.value} yaw={yaw:.3f}")
                except Exception as exc:
                    print(f"jev skipped at {step}: {type(exc).__name__}")

    cam.stop_recording(save_to_filename=str(video_path), fps=30)
    log_json = paths.work_logs / f"{args.run_id}_jev.json"
    log_json.parent.mkdir(parents=True, exist_ok=True)
    import json

    log_json.write_text(json.dumps(decision_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"video -> {video_path}")
    print(f"frames -> {frames_dir}")

    if args.sync_drive:
        dvid = paths.drive_exports_videos
        dvid.mkdir(parents=True, exist_ok=True)
        shutil.copy2(video_path, dvid / video_path.name)
        dframes = paths.drive_exports_frames / args.run_id
        if dframes.exists():
            shutil.rmtree(dframes)
        shutil.copytree(frames_dir, dframes)
        print("synced exports to Drive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
