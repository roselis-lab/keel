"""Draw the generated .pptx to an HTML page, to scale, so the layout can be looked at.

PowerPoint's own export is not available here, and a build that only reports "it fits"
is not the same as seeing it. This reads shape positions, sizes, colours and text back
out of the saved file and lays them out at the same proportions in a browser. Wrapping
and crowding are what it is for; exact glyph metrics will differ from PowerPoint's.

    uv run --with python-pptx python scripts/preview_deck.py [path.pptx]
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

from pptx import Presentation

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/demo/keel-demo.pptx")
OUT = Path("C:/Users/Roselis/AppData/Local/Temp/deck-preview.html")
EMU_IN = 914400
PX_PER_IN = 78.0


def hexcolor(color, fallback: str) -> str:
    try:
        if color is None or color.type is None:
            return fallback
        return "#" + str(color.rgb)
    except Exception:
        return fallback


def px(emu) -> float:
    return round(emu / EMU_IN * PX_PER_IN, 1)


def main() -> int:
    prs = Presentation(str(SRC))
    sw, sh = prs.slide_width, prs.slide_height
    parts = [
        "<html><head><meta charset='utf-8'><style>",
        "body{background:#4a4a52;margin:0;padding:20px;font-family:'Segoe UI',sans-serif}",
        f".s{{position:relative;width:{px(sw)}px;height:{px(sh)}px;margin:0 auto 20px;"
        "overflow:hidden;box-shadow:0 6px 18px #0007}",
        f".n{{color:#e8e8ee;font:12px monospace;width:{px(sw)}px;margin:0 auto 5px}}",
        ".b{position:absolute}",
        "</style></head><body>",
    ]
    for i, slide in enumerate(prs.slides):
        bg = hexcolor(slide.background.fill.fore_color, "#17203a")
        parts.append(f"<div class=n>slide {i}</div><div class=s style='background:{bg}'>")
        for shape in slide.shapes:
            if shape.left is None:
                continue
            box = (f"left:{px(shape.left)}px;top:{px(shape.top)}px;"
                   f"width:{px(shape.width)}px;height:{px(shape.height)}px;")
            if shape.shape_type == 20:      # MSO_SHAPE_TYPE.LINE, a connector
                # Connectors carry no fill and no text, so the generic branch drew them
                # as invisible boxes and the diagram looked like floating labels.
                flip_h = shape.element.spPr.xfrm.get("flipH") == "1"
                flip_v = shape.element.spPr.xfrm.get("flipV") == "1"
                w, h = px(shape.width), px(shape.height)
                x1, x2 = (w, 0) if flip_h else (0, w)
                y1, y2 = (h, 0) if flip_v else (0, h)
                colour = hexcolor(shape.line.color, "#38415f")
                parts.append(
                    f"<svg class=b style=\"{box}overflow:visible\" width='{w}' "
                    f"height='{h}'><defs><marker id='a{i}{id(shape)}' markerWidth='6' "
                    f"markerHeight='6' refX='5' refY='3' orient='auto'>"
                    f"<path d='M0,0 L6,3 L0,6 z' fill='{colour}'/></marker></defs>"
                    f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{colour}' "
                    f"stroke-width='2' marker-end='url(#a{i}{id(shape)})'/></svg>")
                continue
            has_text = shape.has_text_frame and shape.text_frame.text.strip()
            if not has_text:
                try:
                    fill = hexcolor(shape.fill.fore_color, "transparent")
                except Exception:
                    fill = "transparent"
                try:
                    line = (f"border:1px solid {hexcolor(shape.line.color, '#0000')};"
                            if shape.line.fill.type == 1 else "")
                except Exception:
                    line = ""
                parts.append(f"<div class=b style=\"{box}background:{fill};{line}\"></div>")
                continue
            inner = ""
            for para in shape.text_frame.paragraphs:
                text = "".join(r.text for r in para.runs)
                if not para.runs:
                    continue
                if not text:
                    # A blank line in ASCII art is load-bearing. Dropping it here made
                    # the architecture slide look collapsed when the file was fine.
                    text = " "
                run = para.runs[0]
                size = run.font.size.pt if run.font.size else 18
                colour = hexcolor(run.font.color, "#ffffff")
                mono = (run.font.name or "").startswith("Consolas")
                family = "Consolas,monospace" if mono else "'Segoe UI',sans-serif"
                align = {1: "left", 2: "center", 3: "right"}.get(
                    int(para.alignment) if para.alignment is not None else 1, "left")
                weight = "bold " if run.font.bold else ""
                gap = (para.space_before.pt if para.space_before else 0) * PX_PER_IN / 72
                inner += (f"<div style=\"font:{weight}{round(size * PX_PER_IN / 72, 1)}px/1.3 "
                          f"{family};color:{colour};text-align:{align};"
                          f"margin-top:{round(gap, 1)}px;white-space:pre-wrap\">"
                          f"{html.escape(text)}</div>")
            middle = shape.text_frame.vertical_anchor
            justify = "center" if middle == 3 else "flex-start"
            # A shape can carry both a fill and text. Drawing only the text made every
            # box on the architecture slide look like a floating label.
            skin = ""
            try:
                if shape.fill.type == 1:
                    skin += f"background:{hexcolor(shape.fill.fore_color, 'transparent')};"
            except Exception:
                pass
            try:
                if shape.line.fill.type == 1:
                    skin += (f"border:1px solid {hexcolor(shape.line.color, '#0000')};"
                             "border-radius:5px;box-sizing:border-box;")
                elif shape.fill.type == 1:
                    skin += "border-radius:5px;box-sizing:border-box;"
            except Exception:
                pass
            parts.append(f"<div class=b style=\"{box}{skin}display:flex;"
                         f"flex-direction:column;justify-content:{justify}\">{inner}</div>")
        parts.append("</div>")
    parts.append("</body></html>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
