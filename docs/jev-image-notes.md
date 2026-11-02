# Jev 画像対応メモ（2026-11-02 時点の公式ドキュメント）

正本: [Images](https://docs.typesafe.ai/images) · [Box](https://docs.typesafe.ai/primitives/box) · [Blog jev-1.14](https://typesafe.ai/blog/jev-1-14) · SDK [v0.7.5 changelog](https://docs.typesafe.ai/sdk/python/changelog)

## 結論

- **画像入力は使える（実験的 / Danger Zone）**
- **Box（バウンディングボックス）は `jev-1.14.0` が必要**
- `jev-1.13` も画像は受け付けるが Box は不可
- 既定はオフ。毎回ヘッダが必要: `TypeSafe-Danger-Zone-Images: true`
- Models 一覧ページの「Input: Text」表記は遅延している可能性がある。実装は Images ページを正とする

## 使い方（Python SDK）

```python
from pathlib import Path
from typesafe_sdk import Box, Choice, Image, TypeSafeClient

with TypeSafeClient() as client:
    result = client.system_one(
        model="jev-1.14.0",  # Box を使うなら明示推奨
        state={"frame": Image(Path("cam.jpg"))},
        questions={
            "yarn_box": Box(instructions="the yarn ball in `frame`"),
            "action": Choice(
                instructions="Which cat-like action fits `frame`?",
                criteria={
                    "sneak": "Quiet approach.",
                    "walk": "Normal walk.",
                    "pounce": "Short dash toward the target.",
                    "stop": "Stay still.",
                },
            ),
        },
        extra_headers={"TypeSafe-Danger-Zone-Images": "true"},
    )
```

## 制限（抜粋）

| 項目 | 値 |
|---|---|
| 形式 | PNG / JPEG のみ（動画・アニメPNG不可） |
| 1辺 | 280〜1568 px |
| 1枚 | 最大 16 MiB |
| リクエスト全体 | 約 32 MiB |

送信前に Pillow でリサイズ・正立化する（本リポの `image_prep.py`）。
