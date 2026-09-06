"""Render specific PowerPoint slides to PNG via COM automation against the
real, locally installed PowerPoint (2026-08-22 -- the bundled `powerpoint`
Skill's own pptx_render.py needs LibreOffice + poppler for its
soffice-based conversion, and LibreOffice cannot be installed in this
environment; PowerPoint itself IS installed here, and pywin32 is already
present in the Hermes venv from the Outlook integration, so this renders
through the real application instead).

Only use this for slides worth seeing as an image (a real diagram/
architecture visual) -- not a blanket render-every-slide tool.

Usage:
    python render_pptx_slide_win32.py --pptx P --slides 3,12 --outdir DIR

Prints {"rendered": [{"slide": int, "path": str}, ...], "skipped": [int, ...]}
or {"error": str}.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def render_slides(pptx_path: str, slide_numbers: list[int], outdir: str) -> dict:
    import win32com.client

    pptx_abs = os.path.abspath(pptx_path)
    if not os.path.isfile(pptx_abs):
        return {"error": f"pptx not found: {pptx_abs}"}

    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    app = win32com.client.Dispatch("PowerPoint.Application")
    presentation = app.Presentations.Open(pptx_abs, WithWindow=False)
    rendered: list[dict] = []
    skipped: list[int] = []
    try:
        total = presentation.Slides.Count
        for n in slide_numbers:
            if n < 1 or n > total:
                skipped.append(n)
                continue
            slide = presentation.Slides(n)
            out_path = out_dir / f"slide-{n}.png"
            slide.Export(str(out_path), "PNG")
            rendered.append({"slide": n, "path": str(out_path)})
    finally:
        presentation.Close()
        app.Quit()

    return {"rendered": rendered, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pptx", required=True)
    parser.add_argument("--slides", required=True, help="Comma-separated 1-indexed slide numbers, e.g. 3,12,45")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    try:
        slide_numbers = [int(s.strip()) for s in args.slides.split(",") if s.strip()]
    except ValueError:
        print(json.dumps({"error": f"--slides must be comma-separated integers, got: {args.slides!r}"}))
        return 1

    try:
        result = render_slides(args.pptx, slide_numbers, args.outdir)
    except Exception as e:
        result = {"error": f"PowerPoint COM render failed: {e}"}

    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
