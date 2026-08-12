#!/usr/bin/env python3
"""Сжатие JPG меню для витрины: max сторона 960, quality 78."""
from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "menu" / "assets" / "images"
MAX_SIDE = 960
QUALITY = 78


def compress(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, MAX_SIDE / max(w, h))
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        im.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    after = path.stat().st_size
    return before, after


def main() -> None:
    files = sorted(ROOT.rglob("*.jpg"))
    total_b = total_a = 0
    for f in files:
        b, a = compress(f)
        total_b += b
        total_a += a
        print(f"{b/1024:7.0f} -> {a/1024:6.0f} KB  {f.relative_to(ROOT)}")
    print(f"\nTOTAL {total_b/1024/1024:.1f} -> {total_a/1024/1024:.1f} MB "
          f"({100 * total_a / total_b:.0f}%)")


if __name__ == "__main__":
    main()
