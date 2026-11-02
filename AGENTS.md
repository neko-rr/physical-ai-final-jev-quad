# AGENTS.md — PAI最終課題（ネコ型四足 × Genesis × Jev）

> このディレクトリだけを GitHub public に上げる想定。  
> **親リポ（PARC2026）の AGENTS.md は参照しない。** 正本はこのファイル。

| 項目 | 内容 |
|---|---|
| 課題 | Physical AI講座 2026 応用編1 最終課題 |
| 締切 | 2026-11-02（月）AM 10:00 JST |
| 提出 | Omnicampus（レポートPDF + GitHub URL + YouTube） |
| 実行 | Google Colab **G4（約90GB）** |
| テーマ | Genesis Go2 試行（G4 で SIGSEGV）+ **PyBullet Laikago 学習** + 耳尻尾 + **Jev 1.14** で行動選択 |
| 正本/旧 | `docs/current-vs-legacy.md`（提出は正本。旧 RUN は消さない） |

---

## Colab MCP

接続トラブル時: `docs/colab-mcp-connect.md`  
公式: https://github.com/googlecolab/colab-mcp  

Agent からツールが見えないときは、Cursor MCP パネルで **ユーザーが Authenticate** してから「接続して」と指示する。

---

## エージェント向け禁止・必須

### 禁止

- Colab の **起動 / 接続** をユーザー指示なしで行わない
- `.env` 実値・`TYPESAFE_API_KEY`・個人情報を Git / ログ / チャットに出さない
- Drive 上の既存チェックポイントを無断削除しない
- 課題サンプル（Qiita 等）の丸写し提出
- 学習の出力先を Drive の FUSE 直書きだけにしない（遅い・切れやすい）

### 必須

- 学習・重い I/O は **`/content/...`（揮発ローカルSSD）** で行う
- 成果物（CKPT・動画・ログ・環境キャッシュ）は **定期的に Drive へ同期**
- 提出物に氏名・所属・メールを載せない
- 変更前に方針を短く説明し、ユーザー承認を得る（既存ルール踏襲）

---

## リポジトリ構成（GitHub に載せるもの）

```text
.（このフォルダ = Git ルート想定）
├─ AGENTS.md                 # 本ファイル
├─ README.md
├─ .env.example              # キー名のみ
├─ .gitignore
├─ requirements-dev.txt      # PC静的テスト
├─ requirements-colab.txt    # Colab用（軽量ピン）
├─ pytest.ini
├─ src/cat_quad/             # 共有ロジック
├─ tests/
├─ notebooks/                # Colab骨組み（旧は notebooks/legacy/）
├─ scripts/                  # 学習・Jevデモ・同期（正本は pybullet_jev_demo.py）
└─ docs/                     # current-vs-legacy.md 必読
```

**載せない:** `.env`、重み、動画、Genesis clone、`logs/`、`outputs/`、個人情報付きレポート下書き。

---

## Google Drive パス設計（永続）

Colab マウント後のルート:

```text
/content/drive/MyDrive/pai-final-20261102/
```

Drive UI: `マイドライブ` → `pai-final-20261102`（**名前を変えない**）

### ディレクトリ地図

```text
/content/drive/MyDrive/pai-final-20261102/
├─ env/
│  └─ .env.example           # 参考コピー可。実キーは Colab Secrets 推奨
├─ code/                     # 任意: このリポのミラー（git pull or zip展開）
├─ envs/                     # ロボット／シミュ環境の永続キャッシュ
│  ├─ genesis-repo/          # Genesis git clone の退避（任意）
│  ├─ rsl_rl-repo/           # rsl_rl v1.0.2 の退避（任意）
│  ├─ pip-wheels/            # 再DL削減用 wheel キャッシュ（任意）
│  └─ hf-cache/              # Hugging Face キャッシュ（HF_HOME の退避先）
├─ assets/
│  ├─ cat_parts/             # 耳・尻尾 OBJ
│  └─ props/                 # 毛糸玉など小物メッシュ
├─ checkpoints/
│  └─ go2/<run_id>/          # 学習CKPT（last / 定期スナップショット）
├─ exports/
│  ├─ videos/                # 提出用 MP4
│  ├─ frames/                # Jev診断用フレーム
│  └─ reports/               # レポート草稿PDF（個人情報なし）
└─ logs/
   └─ go2/<run_id>/          # tensorboard・stdout 退避
```

### run_id の付け方

`YYYYMMDD-HHMM-<short>` 例: `20261102-0400-go2cat`

同じ run を朝再開するときは **同じ `run_id` を再開**し、新規に上書きしない。

---

## Colab 揮発ディスク（高速 I/O）

ランタイム切断で消える。**作業の主戦場はここ。**

```text
/content/pai_work/                 # WORK_ROOT
├─ Genesis/                        # clone または Drive から rsync
├─ rsl_rl/
├─ cat_quad/                       # src を配置（PYTHONPATH）
├─ assets/                         # Drive からコピーした OBJ 等
├─ checkpoints/                    # 学習の書き込み先（高速）
│  └─ go2/<run_id>/
├─ outputs/
│  ├─ videos/
│  └─ frames/
└─ logs/
```

環境変数（ノート先頭で設定）:

| 変数 | 値 |
|---|---|
| `PAI_DRIVE_ROOT` | `/content/drive/MyDrive/pai-final-20261102` |
| `PAI_WORK_ROOT` | `/content/pai_work` |
| `HF_HOME` | `/content/pai_work/hf-cache`（開始時に Drive `envs/hf-cache` から同期可） |
| `TYPESAFE_API_KEY` | Colab Secrets（userdata）。ノートに直書きしない |

---

## 同期ルール（朝起きてもやり直さない）

1. **開始時（bootstrap）**
   - Drive マウント
   - `PAI_DRIVE_ROOT` が無ければ作成
   - 必要な repo / assets / 最新 CKPT を **Drive → `/content/pai_work`** へコピー（`rsync` or `shutil.copytree`）
2. **学習中**
   - CKPT は **`/content/pai_work/checkpoints/...` に書く**
   - **N 分ごと or epoch ごと**に Drive `checkpoints/go2/<run_id>/` へ同期
   - ログも同様
3. **評価・録画後**
   - MP4 / フレームを Drive `exports/` へコピー
4. **切断検知・セッション終了前**
   - 必ず `scripts/sync_to_drive.py` 相当で CKPT・動画・ログを押し込む

**Drive 直下での長時間 `scene.step` / 学習ループは禁止。**  
読むのも大きな tar は一度 `/content` に展開してから。

---

## AI（Jev）メモ

- モデル: `jev-1.14.0`（Box 利用時）
- ヘッダ: `TypeSafe-Danger-Zone-Images: true`
- 詳細: `docs/jev-image-notes.md`
- SDK: `typesafe-sdk>=0.7.5`

---

## ローカル（PC）作業

```powershell
cd <このフォルダ>
python -m pytest
```

Colab なしで通す範囲: `src/cat_quad` の幾何・前処理・行動決定・モック Jev。

---

## 提出チェック（エージェントはアップロード操作をしない）

- [ ] GitHub **public**（このフォルダ内容）
- [ ] レポート PDF（個人情報なし）
- [ ] YouTube 1〜3分（限定公開以上）
- [ ] Omnicampus Q1〜Q4
- [ ] Drive に最終 CKPT と MP4 が残っている

ユーザーが Omnicampus / YouTube 操作を行う。Agent は提出代行しない。
