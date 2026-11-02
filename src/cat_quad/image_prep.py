"""Jev 画像制限に合わせた前処理。

公式制限: 各辺 280〜1568 px、PNG/JPEG、静止画のみ。
https://docs.typesafe.ai/images
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

MIN_SIDE = 280
MAX_SIDE = 1568


def prepare_image_for_jev(
    source: Path | Image.Image,
    *,
    output_path: Path | None = None,
    format: str = "JPEG",
    quality: int = 90,
) -> Path | Image.Image:
    """EXIF正立 → 長辺<=1568 → 短辺不足ならパディングして下限を満たす。

    output_path があればファイルを書き、その Path を返す。
    無ければ Pillow Image を返す。
    """
    if isinstance(source, Path):
        if not source.is_file():
            raise FileNotFoundError(f"画像がありません: {source}")
        with Image.open(source) as opened:
            img = ImageOps.exif_transpose(opened).convert("RGB")
    else:
        img = ImageOps.exif_transpose(source).convert("RGB")

    # 長辺を上限以内に縮小（拡大はしない）
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)

    w, h = img.size
    if w < MIN_SIDE or h < MIN_SIDE:
        # 短辺が下限未満ならキャンバスを広げて中央配置
        new_w = max(w, MIN_SIDE)
        new_h = max(h, MIN_SIDE)
        canvas = Image.new("RGB", (new_w, new_h), (0, 0, 0))
        canvas.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
        img = canvas

    w, h = img.size
    if w < MIN_SIDE or h < MIN_SIDE or w > MAX_SIDE or h > MAX_SIDE:
        raise ValueError(f"Jev制限外の解像度です: {w}x{h}")

    if output_path is None:
        return img

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_format = "JPEG" if format.upper() in {"JPG", "JPEG"} else "PNG"
    if save_format == "JPEG":
        img.save(output_path, save_format, quality=quality)
    else:
        img.save(output_path, save_format)
    return output_path
