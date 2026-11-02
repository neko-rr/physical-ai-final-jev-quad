#!/usr/bin/env python3
"""Go2 歩行の強化学習（課題提出用・全文）。

Genesis 公式 locomotion 例をベースに、チェックポイントを
`PAI_WORK_ROOT/checkpoints/go2/<run_id>` へ書き、終了時に Drive 同期する。
"""

from __future__ import annotations

import argparse
import os
import pickle
import shutil
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SRC))

from cat_quad.paths import ensure_tree, load_paths  # noqa: E402
from go2_env import Go2Env  # noqa: E402


def _require_rsl() -> None:
    try:
        if int(metadata.version("rsl-rl-lib").split(".")[0]) < 5:
            raise ImportError
    except (metadata.PackageNotFoundError, ImportError, ValueError) as exc:
        raise ImportError("pip install 'rsl-rl-lib>=5.0.0' が必要です") from exc


def get_train_cfg(exp_name: str) -> dict:
    return {
        "algorithm": {
            "class_name": "PPO",
            "clip_param": 0.2,
            "desired_kl": 0.01,
            "entropy_coef": 0.01,
            "gamma": 0.99,
            "lam": 0.95,
            "learning_rate": 0.001,
            "max_grad_norm": 1.0,
            "num_learning_epochs": 5,
            "num_mini_batches": 4,
            "schedule": "adaptive",
            "use_clipped_value_loss": True,
            "value_loss_coef": 1.0,
        },
        "actor": {
            "class_name": "MLPModel",
            "hidden_dims": [512, 256, 128],
            "activation": "elu",
            "distribution_cfg": {
                "class_name": "GaussianDistribution",
                "init_std": 1.0,
                "std_type": "scalar",
            },
        },
        "critic": {
            "class_name": "MLPModel",
            "hidden_dims": [512, 256, 128],
            "activation": "elu",
        },
        "obs_groups": {"actor": ["policy"], "critic": ["policy"]},
        "num_steps_per_env": 24,
        "save_interval": 50,
        "run_name": exp_name,
        "logger": "tensorboard",
    }


def get_cfgs():
    env_cfg = {
        "num_actions": 12,
        "default_joint_angles": {
            "FL_hip_joint": 0.0,
            "FR_hip_joint": 0.0,
            "RL_hip_joint": 0.0,
            "RR_hip_joint": 0.0,
            "FL_thigh_joint": 0.8,
            "FR_thigh_joint": 0.8,
            "RL_thigh_joint": 1.0,
            "RR_thigh_joint": 1.0,
            "FL_calf_joint": -1.5,
            "FR_calf_joint": -1.5,
            "RL_calf_joint": -1.5,
            "RR_calf_joint": -1.5,
        },
        "joint_names": [
            "FR_hip_joint",
            "FR_thigh_joint",
            "FR_calf_joint",
            "FL_hip_joint",
            "FL_thigh_joint",
            "FL_calf_joint",
            "RR_hip_joint",
            "RR_thigh_joint",
            "RR_calf_joint",
            "RL_hip_joint",
            "RL_thigh_joint",
            "RL_calf_joint",
        ],
        "kp": 20.0,
        "kd": 0.5,
        "termination_if_roll_greater_than": 10,
        "termination_if_pitch_greater_than": 10,
        "base_init_pos": [0.0, 0.0, 0.42],
        "base_init_quat": [1.0, 0.0, 0.0, 0.0],
        "episode_length_s": 20.0,
        "resampling_time_s": 4.0,
        "action_scale": 0.25,
        "simulate_action_latency": True,
        "clip_actions": 100.0,
    }
    obs_cfg = {
        "obs_scales": {
            "lin_vel": 2.0,
            "ang_vel": 0.25,
            "dof_pos": 1.0,
            "dof_vel": 0.05,
        },
    }
    reward_cfg = {
        "tracking_sigma": 0.25,
        "base_height_target": 0.3,
        "feet_height_target": 0.075,
        "reward_scales": {
            "tracking_lin_vel": 1.0,
            "tracking_ang_vel": 0.2,
            "lin_vel_z": -1.0,
            "base_height": -50.0,
            "action_rate": -0.005,
            "similar_to_default": -0.1,
        },
    }
    command_cfg = {
        "num_commands": 3,
        "lin_vel_x_range": [0.5, 0.5],
        "lin_vel_y_range": [0, 0],
        "ang_vel_range": [0, 0],
    }
    return env_cfg, obs_cfg, reward_cfg, command_cfg


def main(argv: list[str] | None = None) -> int:
    _require_rsl()
    from rsl_rl.runners import OnPolicyRunner

    import genesis as gs

    parser = argparse.ArgumentParser(description="Train Go2 locomotion for PAI final")
    parser.add_argument("--run-id", default=os.environ.get("RUN_ID", "20261102-0400-go2cat"))
    parser.add_argument("--num-envs", type=int, default=4096)
    parser.add_argument("--max-iterations", type=int, default=101)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--sync-drive", action="store_true", help="学習後に Drive へ CKPT 同期")
    parser.add_argument(
        "--log-to-drive",
        action="store_true",
        help="CKPT を最初から Drive（永続）へ直書き。切断対策",
    )
    args = parser.parse_args(argv)

    paths = load_paths()
    ensure_tree(paths)
    # 切断対策: Drive 直書きを優先
    log_dir = paths.run_drive_ckpt(args.run_id) if args.log_to_drive else paths.run_work_ckpt(args.run_id)
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    env_cfg, obs_cfg, reward_cfg, command_cfg = get_cfgs()
    train_cfg = get_train_cfg(args.run_id)
    if args.log_to_drive:
        train_cfg["save_interval"] = min(int(train_cfg.get("save_interval", 50)), 10)
    with open(log_dir / "cfgs.pkl", "wb") as f:
        pickle.dump([env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg], f)

    print(f"train start run_id={args.run_id} log_dir={log_dir} envs={args.num_envs}")
    gs.init(backend=gs.gpu, precision="32", logging_level="warning", seed=args.seed, performance_mode=True)
    env = Go2Env(
        num_envs=args.num_envs,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=False,
    )
    runner = OnPolicyRunner(env, train_cfg, str(log_dir), device=gs.device)
    runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)
    print("train done")

    if args.sync_drive and not args.log_to_drive:
        dst = paths.run_drive_ckpt(args.run_id)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(log_dir, dst)
        print(f"synced -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
