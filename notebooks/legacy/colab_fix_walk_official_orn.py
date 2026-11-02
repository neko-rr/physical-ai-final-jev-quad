# %% [markdown]
# Colab用: Laikago 公式スポーン姿勢で60秒歩行録画（新規 RUN・履歴非破壊）
#
# 重要:
# - スポーン orn = [0, 0.5, 0.5, 0]（単位クォータニオン禁止→縦向きになる）
# - 学習履歴 `20261102-0745-pybullet-learn` は触らない
# - 出力 RUN = 20261102-0818-walk-official-orn

# %%
from google.colab import drive
drive.mount("/content/drive", force_remount=False)

%pip install -q pybullet imageio imageio-ffmpeg Pillow

import json, math, shutil, subprocess, time
from pathlib import Path
import numpy as np
import pybullet as p
import pybullet_data
from PIL import Image
import imageio.v2 as imageio
from IPython.display import Video, display, HTML

DRIVE = Path("/content/drive/MyDrive/pai-final-20261102")
WORK = Path("/content/pai_work")
RUN = "20261102-0818-walk-official-orn"  # 新規。0745学習は消さない

JOINT_DIRECTIONS = [-1, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1]
JOINT_OFFSETS = [0, -0.7, 0.7, 0, -0.7, 0.7, 0, -0.7, 0.7, 0, -0.7, 0.7]
SPAWN_POS = [0, 0, 0.5]
SPAWN_ORN = [0, 0.5, 0.5, 0]  # 公式
LEG_PHASE = [0.0, math.pi, math.pi, 0.0]

DURATION_S, FPS, SIM_HZ = 60, 30, 240
EVERY = SIM_HZ // FPS
MAX_FRAMES = DURATION_S * FPS
STEPS = DURATION_S * SIM_HZ

for d in [
    WORK / "outputs" / "frames" / RUN,
    WORK / "outputs" / "videos",
    DRIVE / "exports" / "videos",
    DRIVE / "exports" / "frames" / RUN,
    DRIVE / "checkpoints" / "pybullet" / RUN,
]:
    d.mkdir(parents=True, exist_ok=True)

def apply_map(motion):
    return [JOINT_DIRECTIONS[i] * motion[i] + JOINT_OFFSETS[i] for i in range(12)]

def standing():
    return apply_map([0.0] * 12)

def trot(step, amp):
    w = 2 * math.pi * 1.5 * step / SIM_HZ
    motion = [0.0] * 12
    for leg in range(4):
        s = math.sin(w + LEG_PHASE[leg])
        b = leg * 3
        motion[b] = 0.05 * s
        motion[b + 1] = amp * s
        motion[b + 2] = -amp * max(0.0, s)
    return apply_map(motion)

(DRIVE / "checkpoints" / "pybullet" / RUN / "control_ckpt.json").write_text(
    json.dumps(
        {
            "run_id": RUN,
            "spawn_orn": SPAWN_ORN,
            "note": "official orn; does not touch 20261102-0745-pybullet-learn",
            "duration_s": DURATION_S,
        },
        indent=2,
    ),
    encoding="utf-8",
)

cid = p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
p.setTimeStep(1 / SIM_HZ)
p.loadURDF("plane.urdf")
robot = p.loadURDF(
    "laikago/laikago.urdf",
    SPAWN_POS,
    SPAWN_ORN,
    flags=p.URDF_USE_SELF_COLLISION,
)
for j in range(p.getNumJoints(robot)):
    p.changeDynamics(robot, j, linearDamping=0, angularDamping=0)

stand = standing()
for _ in range(480):
    for j, q in enumerate(stand):
        p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=40)
    p.stepSimulation()

frames_dir = WORK / "outputs" / "frames" / RUN
if frames_dir.exists():
    shutil.rmtree(frames_dir)
frames_dir.mkdir(parents=True)

w, h = 640, 480
n_saved = 0
t0 = time.time()
print("START", RUN, "max_frames", MAX_FRAMES, flush=True)
for t in range(STEPS):
    amp = 0.25 * min(1.0, t / 480)
    targets = trot(t, amp)
    for j, q in enumerate(targets):
        p.setJointMotorControl2(robot, j, p.POSITION_CONTROL, targetPosition=q, force=40)
    p.stepSimulation()
    pos, _ = p.getBasePositionAndOrientation(robot)
    if t % EVERY == 0:
        view = p.computeViewMatrixFromYawPitchRoll([pos[0], pos[1], 0.35], 2.8, 30, -18, 0, 2)
        proj = p.computeProjectionMatrixFOV(55, w / h, 0.1, 20)
        _, _, rgb, _, _ = p.getCameraImage(w, h, view, proj, renderer=p.ER_TINY_RENDERER)
        rgb = np.reshape(rgb, (h, w, 4))[:, :, :3].astype(np.uint8)
        Image.fromarray(rgb).save(frames_dir / f"frame_{n_saved:05d}.jpg", quality=85)
        n_saved += 1
        if n_saved % 300 == 0:
            print(f"{n_saved}/{MAX_FRAMES} x={pos[0]:.2f} {time.time()-t0:.1f}s", flush=True)
        if n_saved >= MAX_FRAMES:
            print("HIT MAX — stop", flush=True)
            break
p.disconnect()

vid_work = WORK / "outputs" / "videos" / f"{RUN}.mp4"
vid_drive = DRIVE / "exports" / "videos" / f"{RUN}.mp4"
files = sorted(frames_dir.glob("frame_*.jpg"))
print("encode", len(files), flush=True)
with imageio.get_writer(str(vid_work), fps=FPS, codec="libx264", quality=8) as wr:
    for i, fp in enumerate(files):
        wr.append_data(imageio.imread(fp))
        if i % 300 == 0:
            print("encode", i, flush=True)
shutil.copy2(vid_work, vid_drive)
print("DRIVE", vid_drive, f"{vid_drive.stat().st_size/1e6:.1f}MB")

preview = Path("/content/walk_official_preview.mp4")
subprocess.run(
    ["ffmpeg", "-y", "-i", str(vid_work), "-t", "20", "-vf", "scale=640:-2",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-an", str(preview)],
    capture_output=True,
)
display(HTML(f"<h3>{RUN}</h3><code>{vid_drive}</code>"))
display(Video(str(preview), embed=True, width=640))
