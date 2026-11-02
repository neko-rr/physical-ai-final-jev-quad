# 説明資料 — PAI最終課題

**課題:** Physical AI講座 2026 応用編1 最終課題（AI×ロボティクスによる創造的タスクの実現）  
**タイトル:** Jev が選ぶネコっぽい四足行動（Genesis 試行 + PyBullet + 画像診断）  
**動画:** https://youtu.be/Aprp-QIMXPU （限定公開）  
**コード:** https://github.com/neko-rr/physical-ai-final-jev-quad （public）

> 本資料および成果物に、氏名・所属・メールアドレス等の個人情報は含めません。

---

## 1. 概要・目的

四足ロボットが「毛糸玉」を視覚的に捉え、**行動モード（sneak / walk / pounce / stop）を切り替えて接近・追従する**タスクを設計・実装した。

- **AI（必須）:** TypeSafe **Jev 1.14** による画像診断（推論）。カメラ画像から Choice と Box を得て行動を決定する。
- **学習（任意だが実施）:** シミュレータ上で歩容パラメータを最適化し、制御チェックポイントを保存した。
- **外見:** ネコの耳・尻尾メッシュをアセットとして用意（見た目のネコ化）。

目的は、(1) 学習済み（または最適化済み）の四足歩行、(2) 視覚 AI による行動選択、(3) 1分以上の実行動画、を一連のパイプラインとして再現可能にすることである。

---

## 2. システム構成

| 要素 | 内容 |
|---|---|
| 実行環境 | Google Colab **G4**（NVIDIA RTX PRO 6000 Blackwell, 約96GB） |
| 永続保存 | Google Drive `pai-final-20261102/`（CKPT・動画・Jevログ） |
| 作業 I/O | `/content/pai_work/`（高速領域） |
| シミュレータ | **Genesis**（Go2 PPO を試行）／代替 **PyBullet**（Laikago） |
| 視覚 AI | Jev 1.14 + Danger Zone Images + Box |
| 主要コード | `scripts/pybullet_jev_demo.py`（提出デモ正本） |

### 処理フロー

1. 公式スポーン姿勢で四足を初期化（立位）
2. 前方に赤い球体（毛糸玉）を配置し、ゆっくり移動させる
3. ヘッドレスカメラ画像を取得
4. 数秒ごとに Jev へ画像を渡し、行動モードを更新
5. モードに応じて歩容（周波数・振幅）を切替
6. 画面に `Jev mode: ...` を焼き込み、**75秒程度**の MP4 を保存

---

## 3. 実装の工夫点

### 3.1 Genesis 試行とフォールバック

講義想定の **Genesis Go2 + rsl-rl PPO** を公式例（`plane.urdf` + `RigidOptions`）に合わせて実装・実行した。  
しかし Colab G4（Blackwell）上では学習開始直後に **SIGSEGV** が発生し、`model_*.pt` を得られなかった（公式 locomotion 例でも同症状）。

そこで提出可能性を優先し、**PyBullet Laikago** へ切り替え、歩容パラメータの山登り探索で学習相当の成果物（`control_ckpt.json`）を残した。Genesis 側コードは報告書・再現用にリポジトリへ残している。

### 3.2 シミュレータ姿勢の正しさ

PyBullet 付属 Laikago は、単位クォータニオンでスポーンすると機体が縦向きに見える。  
公式例に合わせ **オリエンテーション `[0, 0.5, 0.5, 0]`** と `jointDirections` / `jointOffsets` を用い、立位から歩行するよう修正した。向きを誤った実験ランは別フォルダに保管し、上書きしない運用とした。

### 3.3 Jev による行動選択

- `src/cat_quad/jev_vision.py` で System One + 画像ヘッダを呼び出す
- Choice を `sneak` / `walk` / `pounce` / `stop` に写像（`behavior.py`）
- デモでは毛糸玉を視野に入れ、Jev 判定結果で歩容ゲインを変更
- 判定ログは Drive の `*_jev.json` に保存（APIキーは Colab Secrets、コード・ログに生値を出さない）

### 3.4 動画要件への対応

課題の動画は **1〜3分**。本実装では **75秒（≥60秒）** を目標に録画し、転倒時は即リセットして「ひっくり返りっぱなしで秒数を稼ぐ」ことを避けた。  
YouTube: https://youtu.be/Aprp-QIMXPU （限定公開）

---

## 4. 主なファイル

| パス | 説明 |
|---|---|
| `scripts/pybullet_jev_demo.py` | 提出デモ（Jev + 歩行 + ≥60秒） |
| `scripts/pybullet_gait_learn.py` | 正しい向きでの歩容学習 |
| `src/cat_quad/` | Jev・行動・歩容・パス・ネコパーツ |
| `scripts/train_go2.py` / `go2_env.py` | Genesis 公式準拠の学習試行 |
| `docs/current-vs-legacy.md` | 正本と旧実験の区別 |
| `tests/` | PC 上の静的テスト（`pytest`） |

---

## 5. 再現手順（要約）

1. Colab で G4 を選択し Drive をマウント
2. Secrets に `TYPESAFE_API_KEY` を登録
3. 本リポジトリを `/content/pai_work/repo` 等へ配置
4. `python scripts/pybullet_gait_learn.py --run-id <run>`（任意・学習）
5. `python scripts/pybullet_jev_demo.py --run-id <run> --duration-s 75`
6. 生成 MP4 と `*_jev.json` を確認

詳細はリポジトリ `README.md` を参照。

---

## 6. 結果と今後

- **できたこと:** Jev 推論を制御ループに組み込んだ四足デモ、1分超の実行動画、学習ログ／CKPT の Drive 永続化、Genesis 公式構成での試行記録。
- **課題:** Genesis の Blackwell 安定化、歩行の転倒低減、Jev 判定の多様化（現状 pounce 偏りあり）、耳尻尾のカメラ映り込み強化。
- **学び:** シミュレーション提出では「学習が通る環境」と「公式アセットの初期姿勢」が成果物品質を左右する。失敗ランを別 ID で残す運用が再実験を助けた。

---

## 7. 提出チェック（自己確認）

- [x] 動画 1〜3分・限定公開以上（本提出: 限定公開 URL 上記）
- [x] コード一式（本リポジトリ）
- [x] 本レポート（PDF化して Omnicampus へ）
- [x] 個人情報を成果物に含めていない
- [ ] GitHub を **public** にし、フォームに URL を記入（提出時）
- [ ] PDF ファイル名を `説明資料_PAI最終課題_<omnicampusアカウント名>.pdf` にする

以上
