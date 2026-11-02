# Colab セッション（厳守）

## 接続中のノート（これだけ）

https://colab.research.google.com/drive/1LWvGjrUoDuOD6lin1l9r9FGzJl97127k

## 禁止

- **新規 notebook を開かない**（empty.ipynb 含む）
- `Start-Process` で Colab URL を開かない
- bridge の first モードでタブを増やさない
- ユーザーが寝ている間に手動許可が必要な操作をしない

## 許可

- 既存ソケットが生きている前提で、セル追加・実行のみ
- Drive 同期・学習は既存ノート上で行う

## 2026-11-02 実績メモ

- Genesis Go2 PPO: G4 Blackwell で SIGSEGV（`model_*.pt` 未作成）
- PyBullet 学習履歴: `checkpoints/pybullet/20261102-0745-pybullet-learn/`（残す・上書き禁止）
- Laikago 動画: スポーンは公式 `[0,0.5,0.5,0]`。単位クォータニオンは縦向きになる
- 新規録画は必ず新しい RUN ID を使う
