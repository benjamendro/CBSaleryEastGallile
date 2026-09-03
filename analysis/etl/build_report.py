#!/usr/bin/env python3
"""Assemble analysis/report.html from its three sources plus the data blob.

    head.html   <head>, styles
    body.html   all prose sections and the empty <svg> placeholders
    charts.js   the drawing code, reading window.__D__

Run after any edit to those files or to output/report_data.json:
    python3 analysis/etl/build_report.py
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "src", ROOT / "output"

data = json.loads((OUT / "report_data.json").read_text(encoding="utf-8"))
blob = json.dumps(data, ensure_ascii=False)

html = "".join([
    (SRC / "head.html").read_text(encoding="utf-8"),
    (SRC / "body.html").read_text(encoding="utf-8"),
    f"\n<script>window.__D__={blob};</script>\n",
    (SRC / "charts.js").read_text(encoding="utf-8"),
])
(ROOT / "report.html").write_text(html, encoding="utf-8")
print(f"report.html  {len(html):,} bytes  ·  {html.count(chr(10)):,} lines")
