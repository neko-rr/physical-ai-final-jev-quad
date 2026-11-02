# %% [markdown]
# PAI最終課題 Colab骨組み — Genesis Go2 + ネコ耳尻尾 + Jev画像診断
#
# **このファイルは未実行。** ユーザーが「起動 / 接続」と言うまで Colab には繋がない。
# パス設計の正本: リポジトリ直下 `AGENTS.md`

# %%
# セル0: Drive マウント + パス（永続は Drive、作業は /content）
# from google.colab import drive
# drive.mount("/content/drive")
#
# import os
# from pathlib import Path
#
# os.environ["PAI_DRIVE_ROOT"] = "/content/drive/MyDrive/pai-final-20261102"
# os.environ["PAI_WORK_ROOT"] = "/content/pai_work"
# os.environ["HF_HOME"] = "/content/pai_work/hf-cache"
# RUN_ID = "20261102-0400-go2cat"  # 再開時は同じ ID

# %%
# セル1: ランタイム確認（G4想定）
# !nvidia-smi

# %%
# セル2: このリポを work へ配置（GitHub clone または Drive/code から）
# !mkdir -p /content/pai_work
# # 例: !git clone https://github.com/<user>/<repo>.git /content/pai_work/repo
# # import sys; sys.path.insert(0, "/content/pai_work/repo/src")

# %%
# セル3: bootstrap（ディレクトリ作成・Drive→content）
# %cd /content/pai_work/repo
# !python scripts/sync_io.py bootstrap --run-id $RUN_ID

# %%
# セル4: 秘密（キーを表示しない）
# from google.colab import userdata
# import os
# os.environ["TYPESAFE_API_KEY"] = userdata.get("TYPESAFE_API_KEY")
# # 任意: os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")

# %%
# セル5: 依存関係（torch は Colab 既定を優先）
# %pip install -q -r requirements-colab.txt
# # Genesis / rsl_rl は work 配下へ
# # !git clone --depth 1 https://github.com/Genesis-Embodied-AI/Genesis.git /content/pai_work/Genesis
# # !git clone --depth 1 --branch v1.0.2 https://github.com/leggedrobotics/rsl_rl.git /content/pai_work/rsl_rl
# # %pip install -q -e /content/pai_work/rsl_rl
# # 環境の退避（任意・時間に余裕があれば）
# # !rsync -a /content/pai_work/Genesis/ "$PAI_DRIVE_ROOT/envs/genesis-repo/"

# %%
# セル6: ネコパーツを work & Drive へ
# from cat_quad.cat_parts import export_cat_parts
# from cat_quad.paths import load_paths
# paths = load_paths()
# export_cat_parts(paths.work_assets / "cat_parts")
# export_cat_parts(paths.drive_assets / "cat_parts")

# %%
# セル7: Go2 学習（書き込みは /content。定期的に Drive 同期）
# %cd /content/pai_work/Genesis
# # CKPT 出力先を /content/pai_work/checkpoints/go2/$RUN_ID に向ける（公式スクリプト要調整）
# # !python examples/locomotion/go2_train.py
# # 学習ループの合間・終了時:
# # !python /content/pai_work/repo/scripts/sync_io.py push-ckpt --run-id $RUN_ID
# # !python /content/pai_work/repo/scripts/sync_io.py push-hf-cache

# %%
# セル8: 評価 + 録画（MP4 は work/outputs/videos → すぐ Drive へ）
# # !python examples/locomotion/go2_eval.py
# # !python /content/pai_work/repo/scripts/sync_io.py push-exports

# %%
# セル9: Jev 画像診断
# from pathlib import Path
# from cat_quad.jev_vision import analyze_frame, build_live_client
# client = build_live_client()
# decision = analyze_frame(
#     client,
#     Path("/content/pai_work/outputs/frames/frame000.jpg"),
#     prepared_dir=Path("/content/pai_work/outputs/frames/jev_prep"),
# )
# print(decision.mode, decision.yaw_rad)

# %%
# セル10: セッション終了前の必須同期
# # !python /content/pai_work/repo/scripts/sync_io.py push-ckpt --run-id $RUN_ID
# # !python /content/pai_work/repo/scripts/sync_io.py push-exports
# # !python /content/pai_work/repo/scripts/sync_io.py push-hf-cache
