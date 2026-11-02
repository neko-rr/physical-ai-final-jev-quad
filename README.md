# PAI最終課題 — Jev が選ぶネコっぽい四足行動

Physical AI講座 2026 応用編1 最終課題の提出用リポジトリです。

| 項目 | 内容 |
|---|---|
| GitHub（public） | https://github.com/neko-rr/physical-ai-final-jev-quad |
| 動画（限定公開） | https://youtu.be/Aprp-QIMXPU |
| レポート原稿 | [`reports/説明資料_PAI最終課題.md`](./reports/説明資料_PAI最終課題.md)（PDF化して提出） |
| 正本と旧の区別 | [`docs/current-vs-legacy.md`](./docs/current-vs-legacy.md) |
| エージェント向け | [`AGENTS.md`](./AGENTS.md) |

**個人情報（氏名・所属・メール等）はリポジトリに含めていません。**

---

## 何をしたか

1. **Genesis Go2 PPO** を公式 locomotion 構成で試行（Colab G4）→ SIGSEGV で重み未取得  
2. **PyBullet Laikago** で歩容パラメータを学習（正しいスポーン姿勢）  
3. 前方の **毛糸玉** をカメラで捉え、**Jev 1.14** が `sneak/walk/pounce/stop` を選択して歩容を切替  
4. **1分以上**の実行動画を YouTube 限定公開

---

## リポジトリ構成

```text
src/cat_quad/          # Jev・行動・歩容・パス・ネコパーツ
scripts/
  pybullet_jev_demo.py # ★提出デモ正本（Jev + ≥60秒）
  pybullet_gait_learn.py
  train_go2.py         # Genesis 試行
  go2_env.py           # 公式 plane.urdf + RigidOptions
tests/                 # PC 静的テスト
notebooks/             # Colab 骨組み（旧は legacy/）
reports/               # レポート原稿
docs/                  # 手順・正本/旧の表
```

---

## すばやく動かす（Colab）

1. ランタイム **G4**、Drive マウント  
2. Secrets に `TYPESAFE_API_KEY`  
3. 本リポを配置したうえで:

```bash
python scripts/pybullet_gait_learn.py --run-id 20261102-0822-pybullet-learn-orn
python scripts/pybullet_jev_demo.py --run-id 20261102-0830-jev-walk-75s --duration-s 75
```

成果は Drive `pai-final-20261102/exports/videos/` と `logs/` へ保存されます。

---

## PC 静的テスト

```powershell
cd <このフォルダ>
python -m pytest
```

---

## Omnicampus 提出チェック

- [x] YouTube: https://youtu.be/Aprp-QIMXPU （限定公開）
- [ ] 公開状況フォーム: `限定公開対応`
- [ ] レポート PDF（`reports/説明資料_PAI最終課題.md` を PDF 化。ファイル名に omnicampus アカウント名）
- [x] GitHub **public**: https://github.com/neko-rr/physical-ai-final-jev-quad
- [x] 個人情報なし → フォームに `確認しました`

---

## ライセンス・出典

Genesis 公式例の取り込み範囲は [`third_party/NOTICE.md`](./third_party/NOTICE.md) を参照。
