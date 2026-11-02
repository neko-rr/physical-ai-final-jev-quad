# このセルだけを、接続済みノートに貼って実行してください。
# ノート URL: https://colab.research.google.com/drive/1LWvGjrUoDuOD6lin1l9r9FGzJl97127k
# 学習完了後、CKPT は Drive の pai-final-20261102/checkpoints/go2/ に残ります。
# 動画撮影は朝でOK。

from google.colab import drive
from pathlib import Path
import os, shutil, sys, subprocess

drive.mount("/content/drive", force_remount=False)

os.environ["PAI_DRIVE_ROOT"] = "/content/drive/MyDrive/pai-final-20261102"
os.environ["PAI_WORK_ROOT"] = "/content/pai_work"
os.environ["HF_HOME"] = "/content/pai_work/hf-cache"
RUN_ID = "20261102-0400-go2cat"
os.environ["RUN_ID"] = RUN_ID

drive_root = Path(os.environ["PAI_DRIVE_ROOT"])
work_root = Path(os.environ["PAI_WORK_ROOT"])
drive_root.mkdir(parents=True, exist_ok=True)
work_root.mkdir(parents=True, exist_ok=True)

# 課題コード: Drive の code/repo を /content へ（無ければエラーで止める）
drive_repo = drive_root / "code" / "repo"
work_repo = work_root / "repo"
assert (drive_repo / "scripts" / "train_go2.py").is_file(), (
    f"先に PC の 20261102-physical-ai-final を {drive_repo} にアップロードしてください"
)
if work_repo.exists():
    shutil.rmtree(work_repo)
shutil.copytree(drive_repo, work_repo)
sys.path.insert(0, str(work_repo / "src"))
sys.path.insert(0, str(work_repo / "scripts"))
os.chdir(work_repo)
print("REPO", work_repo)

subprocess.check_call([sys.executable, "scripts/setup_colab_env.py"])
subprocess.check_call([sys.executable, "scripts/sync_io.py", "bootstrap", "--run-id", RUN_ID])

# Secrets（未設定なら学習のみ続行）
try:
    from google.colab import userdata
    os.environ["TYPESAFE_API_KEY"] = userdata.get("TYPESAFE_API_KEY")
    print("TYPESAFE_API_KEY: set")
except Exception as e:
    print("TYPESAFE_API_KEY skip:", type(e).__name__)

# ===== 学習（ここが一番重い）=====
subprocess.check_call(
    [
        sys.executable,
        "scripts/train_go2.py",
        "--run-id",
        RUN_ID,
        "--num-envs",
        "4096",
        "--max-iterations",
        "101",
        "--sync-drive",
    ]
)
print("TRAIN DONE — CKPT on Drive. Video can wait until morning.")
print("drive ckpt:", drive_root / "checkpoints" / "go2" / RUN_ID)
