"""ネコ耳・尻尾の簡易メッシュ生成（OBJ）。

Go2 本体は犬型だが、頭部に三角耳、臀部に曲線尻尾を載せると
動画上はネコに見える、という最短の見た目ハック。
Genesis 側では別 entity として読み込み、リンク姿勢に追従させる想定。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MeshData:
    """三角形メッシュ（頂点・面インデックス）。"""

    vertices: np.ndarray  # (N, 3) float64
    faces: np.ndarray  # (M, 3) int64


@dataclass(frozen=True)
class CatPartMeshes:
    left_ear: MeshData
    right_ear: MeshData
    tail: MeshData


def _cone(n_sides: int = 12, height: float = 0.08, radius: float = 0.03) -> MeshData:
    """Z+向きの簡易円錐（耳用）。"""
    if n_sides < 3:
        raise ValueError("n_sides は 3 以上")
    angles = np.linspace(0.0, 2.0 * np.pi, n_sides, endpoint=False)
    base = np.column_stack(
        [radius * np.cos(angles), radius * np.sin(angles), np.zeros(n_sides)]
    )
    tip = np.array([[0.0, 0.0, height]], dtype=np.float64)
    vertices = np.vstack([base, tip])
    tip_i = n_sides
    faces = []
    for i in range(n_sides):
        j = (i + 1) % n_sides
        faces.append([i, j, tip_i])
    return MeshData(vertices=vertices, faces=np.asarray(faces, dtype=np.int64))


def _tail_tube(
    *,
    segments: int = 16,
    length: float = 0.35,
    radius: float = 0.015,
    curl: float = 0.55,
    radial: int = 8,
) -> MeshData:
    """XZ 平面で曲がる細いチューブ（尻尾）。"""
    if segments < 2 or radial < 3:
        raise ValueError("segments/radial が不正です")

    ts = np.linspace(0.0, 1.0, segments)
    # 付け根から後ろへ伸びつつ上へカール
    centers = np.column_stack(
        [
            np.zeros(segments),
            -length * ts,
            curl * length * (ts**2),
        ]
    )

    ring_angles = np.linspace(0.0, 2.0 * np.pi, radial, endpoint=False)
    ring = np.column_stack(
        [radius * np.cos(ring_angles), np.zeros(radial), radius * np.sin(ring_angles)]
    )

    verts: list[np.ndarray] = []
    for c in centers:
        verts.append(ring + c)
    vertices = np.vstack(verts)

    faces: list[list[int]] = []
    for s in range(segments - 1):
        for r in range(radial):
            a = s * radial + r
            b = s * radial + (r + 1) % radial
            c = (s + 1) * radial + (r + 1) % radial
            d = (s + 1) * radial + r
            faces.append([a, b, c])
            faces.append([a, c, d])

    return MeshData(vertices=vertices, faces=np.asarray(faces, dtype=np.int64))


def build_cat_parts(
    *,
    ear_height: float = 0.09,
    ear_radius: float = 0.028,
    ear_separation: float = 0.06,
    ear_n_sides: int = 12,
) -> CatPartMeshes:
    """左右の耳と尻尾メッシュを返す。ローカル座標は各パーツ原点基準。"""
    ear = _cone(n_sides=ear_n_sides, height=ear_height, radius=ear_radius)
    # 配置用オフセットは呼び出し側 / OBJ 書き出し時に適用してもよいが、
    # ここでは左右で符号違いの X 平行移動を焼き込む
    left_v = ear.vertices.copy()
    left_v[:, 0] -= ear_separation / 2.0
    right_v = ear.vertices.copy()
    right_v[:, 0] += ear_separation / 2.0
    return CatPartMeshes(
        left_ear=MeshData(vertices=left_v, faces=ear.faces.copy()),
        right_ear=MeshData(vertices=right_v, faces=ear.faces.copy()),
        tail=_tail_tube(),
    )


def write_obj(mesh: MeshData, path: Path) -> Path:
    """Wavefront OBJ を書き出す。"""
    path = Path(path)
    if path.suffix.lower() != ".obj":
        raise ValueError("拡張子は .obj にしてください")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# cat_quad generated mesh", "o cat_part"]
    for v in mesh.vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    for f in mesh.faces:
        # OBJ は 1-based
        lines.append(f"f {f[0] + 1} {f[1] + 1} {f[2] + 1}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def export_cat_parts(output_dir: Path) -> dict[str, Path]:
    """耳・尻尾 OBJ をディレクトリへ書き出す。"""
    output_dir = Path(output_dir)
    parts = build_cat_parts()
    return {
        "left_ear": write_obj(parts.left_ear, output_dir / "cat_left_ear.obj"),
        "right_ear": write_obj(parts.right_ear, output_dir / "cat_right_ear.obj"),
        "tail": write_obj(parts.tail, output_dir / "cat_tail.obj"),
    }
