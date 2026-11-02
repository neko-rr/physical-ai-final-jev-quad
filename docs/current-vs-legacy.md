# 正本（最新）と旧コード・旧実験の区別

提出・GitHub 公開時は **正本だけを説明の中心**にする。旧は履歴・失敗分析用。

## 提出用正本（最新・正しい前提）

| 役割 | パス | 要点 |
|---|---|---|
| Jev+歩行デモ | `scripts/pybullet_jev_demo.py` | 公式スポーン orn、毛糸玉、Jev切替、**75秒（≥60秒）**、Drive直書き |
| 歩容学習 | `scripts/pybullet_gait_learn.py` | 正しい向きで山登り。`0745` は触らない |
| 歩容ロジック | `src/cat_quad/pybullet_gait.py` | orn=`[0,0.5,0.5,0]`、jointOffsets/Directions |
| Jev | `src/cat_quad/jev_vision.py` + `behavior.py` | Choice→行動モード |
| Genesis試行 | `scripts/train_go2.py` / `go2_env.py` | 公式 `plane.urdf`+RigidOptions。G4 では SIGSEGV で重み未取得 |
| Colabノート | `notebooks/cat_go2_jev.ipynb` | 手順の骨組み |
| 静的テスト | `tests/` | `python -m pytest` |

### Drive 上の推奨成果（正本ラン）

| RUN | 内容 |
|---|---|
| `20261102-0822-pybullet-learn-orn` | 正しい向きでの学習 CKPT |
| `20261102-0830-jev-walk-75s` | Jev 込み 75秒動画・jev.json（提出候補） |

## 旧・失敗・参考（消さない／上書きしない）

| 区分 | 例 | 理由 |
|---|---|---|
| 向き誤り学習 | `.../20261102-0745-pybullet-learn/` | 単位クォータニオン。縦向き・報酬マイナス |
| Jevなし長尺 | `20261102-0741-pybullet-90s` / `0803-walk-90s` | Jev未接続 or 姿勢不良 |
| Genesis | `checkpoints/go2/*/cfgs.pkl` only | SIGSEGV、`model_*.pt` なし |
| 旧ノート | `notebooks/legacy/` | 初期骨組み・一晩学習セル・向き修正のみセル |

## やってはいけないこと

- `0745-pybullet-learn` のフォルダを消す／上書きする
- 単位クォータニオン `[0,0,0,1]` で Laikago をスポーンする
- 60秒未満の動画を提出正本にする
- Colab 学習用 requirements を提出物説明に混ぜてキーを載せる
