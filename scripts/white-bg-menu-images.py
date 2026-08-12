#!/usr/bin/env python3
"""Batch-convert menu JPGs to a pure white studio background.

Designed for the MarketingCofe menu assets where the product is centered
against a soft beige backdrop. Uses GrabCut plus border-color cleanup so we
keep the cup/food, preserve a soft contact shadow, and normalize the backdrop
to #FFFFFF.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent / "menu" / "assets" / "images"


def build_alpha_mask(bgr: np.ndarray) -> np.ndarray:
    h, w = bgr.shape[:2]

    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    margin_x = max(18, int(w * 0.08))
    margin_y = max(18, int(h * 0.08))
    rect = (margin_x, margin_y, w - margin_x * 2, h - margin_y * 2)
    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    fg = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype(np.uint8)

    # Clean the mask but avoid cutting holes into transparent cups / whipped cream.
    fg = cv2.morphologyEx(
        fg,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        iterations=1,
    )
    fg = cv2.morphologyEx(
        fg,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1,
    )

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
    if num_labels > 1:
        cx0, cy0 = w / 2.0, h / 2.0
        best_label = 1
        best_score = float("-inf")
        for label in range(1, num_labels):
            x, y, ww, hh, area = stats[label]
            cx = x + ww / 2.0
            cy = y + hh / 2.0
            center_score = -(((cx - cx0) / w) ** 2 + ((cy - cy0) / h) ** 2) * 4000
            area_score = area
            score = center_score + area_score
            if score > best_score:
                best_score = score
                best_label = label
        fg = np.where(labels == best_label, 255, 0).astype(np.uint8)

    fg = cv2.GaussianBlur(fg, (0, 0), 1.6)
    return fg


def synthetic_shadow(size: tuple[int, int], alpha: np.ndarray) -> Image.Image:
    h, w = size
    ys, xs = np.where(alpha > 24)
    shadow = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    if len(xs) == 0 or len(ys) == 0:
        return shadow

    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    obj_w = x1 - x0 + 1
    obj_h = y1 - y0 + 1
    cx = (x0 + x1) / 2
    cy = min(h - 18, y1 + obj_h * 0.08)
    rx = max(28, int(obj_w * 0.42))
    ry = max(10, int(obj_h * 0.06))

    yy, xx = np.mgrid[0:h, 0:w]
    norm = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    ellipse = np.clip(1.0 - norm, 0.0, 1.0)
    ellipse = cv2.GaussianBlur((ellipse * 255).astype(np.uint8), (0, 0), 10.0)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = 0
    rgba[..., 3] = (ellipse * 0.22).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def process_image(path: Path, out_path: Path) -> None:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise RuntimeError(f"Cannot read image: {path}")

    alpha = build_alpha_mask(bgr)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha])

    base = Image.new("RGBA", (rgba.shape[1], rgba.shape[0]), (255, 255, 255, 255))
    base = Image.alpha_composite(base, synthetic_shadow((rgba.shape[0], rgba.shape[1]), alpha))
    fg = Image.fromarray(rgba, "RGBA")
    composed = Image.alpha_composite(base, fg).convert("RGB")

    composed = ImageEnhance.Contrast(composed).enhance(1.06)
    composed = ImageEnhance.Color(composed).enhance(1.03)
    composed = ImageEnhance.Sharpness(composed).enhance(1.08)
    composed = composed.filter(ImageFilter.UnsharpMask(radius=1.2, percent=108, threshold=2))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed.save(out_path, "JPEG", quality=92, optimize=True, progressive=True)


def iter_files(kind: str) -> list[Path]:
    if kind == "drinks":
        return sorted((ROOT / "drinks").glob("*.jpg"))
    if kind == "food":
        return sorted((ROOT / "food").glob("*.jpg"))
    return sorted(ROOT.rglob("*.jpg"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["all", "drinks", "food"], default="all")
    parser.add_argument("--in-place", action="store_true", dest="in_place")
    parser.add_argument("--output", type=Path, default=ROOT.parent / "images-white-preview")
    parser.add_argument("paths", nargs="*", help="Optional specific JPG files")
    args = parser.parse_args()

    files = [Path(p) for p in args.paths] if args.paths else iter_files(args.kind)
    if not files:
        raise SystemExit("No input JPG files found.")

    for src in files:
        out = src if args.in_place else args.output / src.relative_to(ROOT)
        process_image(src, out)
        print(f"OK {src.name} -> {out}")


if __name__ == "__main__":
    main()
