"""One picture per finding: who, the way in, the weak spot, the damage, and where the fix
cuts the chain.

A picture carries one relationship, so this draws the chain and nothing else; the rest of
the finding stays in text beside it. It is a PNG because Confluence Cloud does not show
an attached SVG reliably and both Confluence and Jira show a PNG everywhere.

Reports can be written in any language, and the font Pillow ships has Latin letters only,
so a Russian report would come out as empty boxes. The picture uses the first system font
found that also covers Cyrillic (DejaVu Sans on Linux, Arial or Segoe UI on Windows, Arial
on macOS). `KEEL_PICTURE_FONT` names a `.ttf` file to use instead, for a picture that is
the same on every machine.
"""
from __future__ import annotations

import functools
import io
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from keel.schemas.report import Finding, Report

SCALE = 2  # drawn at twice the size so it stays sharp on high-density screens
INK = (23, 43, 77)
MUTED = (94, 108, 132)
EDGE = (193, 199, 208)
FILL = (244, 245, 247)
FIX = (0, 82, 204)
FIX_FILL = (222, 235, 255)
SEVERITY_EDGE = {"high": (222, 53, 11), "medium": (255, 139, 0), "low": (54, 179, 126)}
SEVERITY_FILL = {"high": (255, 244, 240), "medium": (255, 250, 230), "low": (227, 252, 239)}


_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf"),
    str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"),
)


@functools.cache
def font_file() -> str | None:
    """The font the picture is drawn with, or None when no font with Cyrillic is found."""
    pinned = os.environ.get("KEEL_PICTURE_FONT")
    if pinned:
        return pinned
    return next((p for p in _FONT_CANDIDATES if Path(p).is_file()), None)


def _font(size: int):
    path = font_file()
    if path:
        return ImageFont.truetype(path, size * SCALE)
    return ImageFont.load_default(size=size * SCALE)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def way_in(report: Report, finding: Finding) -> str:
    """The surface the finding crosses, from the ledger; the first one if several."""
    for s in report.surfaces:
        if finding.id in s.outcome:
            return f"{s.name} ({s.where})"
    return "not named in the ledger"


def steps(report: Report, finding: Finding, vocab: dict[str, dict[str, Any]]) -> list[tuple[str, str, str]]:
    def name(kind: str, key: str | None) -> str:
        if not key:
            return ""
        return (vocab.get(kind, {}).get(key) or {}).get("name") or key

    return [
        ("WHO", name("source", finding.source.who), finding.source.access),
        ("WAY IN", way_in(report, finding), name("surface", finding.attack_surface)),
        ("WEAK SPOT", finding.vulnerability, ""),
        ("DAMAGE", name("harm", finding.harm), finding.asset),
    ]


def chain_png(
    report: Report, finding: Finding, vocab: dict[str, dict[str, Any]], fix: str | None
) -> bytes:
    s = SCALE
    chain = steps(report, finding, vocab)
    box_w, gap, top, pad = 230 * s, 52 * s, 40 * s, 14 * s
    width = 4 * box_w + 3 * gap + 40 * s
    body, small, lab = _font(16), _font(13), _font(13)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def block(main: str, sub: str) -> int:
        h = len(_wrap(probe, main, body, box_w - 2 * pad)) * 21 * s
        if sub:
            h += 8 * s + len(_wrap(probe, sub, small, box_w - 2 * pad)) * 18 * s
        return h + 2 * pad

    box_h = max(block(m, sub) for _, m, sub in chain)
    fix_lines = _wrap(probe, f"FIX HERE: {fix}", small, width - 80 * s) if fix else []
    fix_h = (30 * s + len(fix_lines) * 18 * s + 2 * pad) if fix else 0
    height = top + box_h + fix_h + 12 * s

    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    sev = finding.risk.severity
    x0 = 20 * s
    centers = []
    for i, (label, main, sub) in enumerate(chain):
        x = x0 + i * (box_w + gap)
        last = i == len(chain) - 1
        d.rounded_rectangle(
            [x, top, x + box_w, top + box_h], radius=8 * s,
            fill=SEVERITY_FILL[sev] if last else FILL,
            outline=SEVERITY_EDGE[sev] if last else EDGE, width=2 * s,
        )
        d.text((x, top - 22 * s), f"{i + 1}  {label}", font=lab, fill=MUTED)
        y = top + pad
        for line in _wrap(d, main, body, box_w - 2 * pad):
            d.text((x + pad, y), line, font=body, fill=INK)
            y += 21 * s
        if sub:
            y += 8 * s
            for line in _wrap(d, sub, small, box_w - 2 * pad):
                d.text((x + pad, y), line, font=small, fill=MUTED)
                y += 18 * s
        centers.append(x + box_w // 2)
        if not last:
            ay = top + box_h // 2
            ax, bx = x + box_w + 8 * s, x + box_w + gap - 8 * s
            d.line([ax, ay, bx - 10 * s, ay], fill=MUTED, width=3 * s)
            d.polygon([(bx, ay), (bx - 12 * s, ay - 7 * s), (bx - 12 * s, ay + 7 * s)], fill=MUTED)

    if fix:
        # The fix closes the weak spot, so it hangs from box 3.
        cx, y1 = centers[2], top + box_h
        d.line([cx, y1, cx, y1 + 22 * s], fill=FIX, width=3 * s)
        text_w = max(d.textlength(line, font=small) for line in fix_lines)
        w = text_w + 2 * pad
        bx0 = max(x0, min(cx - w / 2, width - x0 - w))
        d.rounded_rectangle(
            [bx0, y1 + 22 * s, bx0 + w, y1 + 22 * s + len(fix_lines) * 18 * s + 2 * pad],
            radius=6 * s, fill=FIX_FILL, outline=FIX, width=2 * s,
        )
        y = y1 + 22 * s + pad
        for line in fix_lines:
            d.text((bx0 + pad, y), line, font=small, fill=FIX)
            y += 18 * s

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
